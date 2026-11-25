"""Form input encoded the way each field's widget reads it.

Two layers, tested separately on purpose:

* :mod:`cms.forms.widget_data` on its own, against widgets declared here. The
  interesting widgets are other people's -- a MultiWidget from
  djangocms-frontend, an attributes widget, a bespoke indexed one in a
  project's own package -- so the tests declare the *shapes* rather than depending on any of
  them being installed.
* :meth:`~cms.core.plugin_base.CMSPluginBase.clean_plugin_data`, which is where
  a caller with no browser meets a form that expects one.
"""

from unittest.mock import patch

from django import forms
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.utils.datastructures import MultiValueDict

from cms.api import add_plugin, create_page
from cms.forms.widget_data import (
    as_widget_data,
    declared_inverse_is_sound,
    posted_values,
    refuse_unreadable,
    unreadable,
)
from cms.test_utils.project.pluginapp.plugins.link.cms_plugins import LinkPlugin
from cms.test_utils.project.pluginapp.plugins.link.models import Link
from cms.test_utils.testcases import CMSTestCase


# ---------------------------------------------------------------------------
# widgets standing in for the shapes that exist in the wild
# ---------------------------------------------------------------------------
class PairWidget(forms.MultiWidget):
    """A MultiWidget, the shape djangocms-frontend's spacing and title fields use."""

    def __init__(self, **kwargs):
        kwargs.setdefault("widgets", (forms.TextInput(), forms.TextInput()))
        super().__init__(**kwargs)

    def decompress(self, value):
        if isinstance(value, dict):
            return [value.get("left", ""), value.get("right", "")]
        return ["", ""]


class PairField(forms.MultiValueField):
    def __init__(self, **kwargs):
        kwargs.setdefault(
            "fields", (forms.CharField(required=False), forms.CharField(required=False))
        )
        kwargs.setdefault("require_all_fields", False)
        kwargs.setdefault("widget", PairWidget())
        super().__init__(**kwargs)

    def compress(self, data_list):
        if not data_list:
            return {}
        return {"left": data_list[0], "right": data_list[1]}


class IndexedWidget(forms.Widget):
    """Reads ``<name>__<i>`` keys and nothing else, with no inverse declared.

    The shape of a bespoke widget in a project's own package: it never looks at
    ``data[name]``, so the obvious value is invisible to it.
    """

    def value_from_datadict(self, data, files, name):
        prefix = f"{name}__"
        return [data[key] for key in sorted(data) if key.startswith(prefix)]


class DeclaredIndexedWidget(IndexedWidget):
    """The same protocol, with the inverse declared beside the decoder."""

    def value_to_datadict(self, name, value):
        return {f"{name}__{index}": item for index, item in enumerate(value or ())}


class ExplodingWidget(forms.Widget):
    def value_from_datadict(self, data, files, name):
        raise RuntimeError("this widget cannot read anything")


class PostedValuesTest(SimpleTestCase):
    """What a browser would have posted under one field's own key."""

    def test_none_is_nothing_posted_rather_than_the_value_none(self):
        field = forms.MultipleChoiceField(choices=[("a", "A")])
        self.assertEqual(posted_values(field, None), [])

    def test_empty_string_is_nothing_for_a_field_taking_several_values(self):
        field = forms.MultipleChoiceField(choices=[("a", "A")])
        self.assertEqual(posted_values(field, ""), [])

    def test_empty_string_is_a_real_submission_for_a_scalar_field(self):
        self.assertEqual(posted_values(forms.CharField(), ""), [""])

    def test_a_list_is_spread_for_a_field_taking_several_values(self):
        field = forms.MultipleChoiceField(choices=[("a", "A"), ("b", "B")])
        self.assertEqual(posted_values(field, ["a", "b"]), ["a", "b"])

    def test_a_list_is_one_value_for_a_scalar_field(self):
        # A JSONField holding an array. Spreading it would hand the field the
        # array's last element instead of the array.
        self.assertEqual(posted_values(forms.JSONField(), [1, 2]), [[1, 2]])

    def test_an_empty_list_is_nothing_posted_for_a_scalar_field(self):
        # MultiValueDict.get returns its default for a stored [], so [[]] would
        # satisfy getlist and read back as None through get.
        self.assertEqual(posted_values(forms.CharField(), []), [])

    def test_a_field_this_encoder_has_never_seen_still_posts_its_value(self):
        self.assertEqual(posted_values(None, "x"), ["x"])


class AsWidgetDataTest(SimpleTestCase):
    def test_the_callers_own_key_is_always_kept(self):
        fields = {"name": forms.CharField()}
        encoded = as_widget_data(fields, {"name": "Lizzie"})
        self.assertEqual(encoded.get("name"), "Lizzie")

    def test_a_multiwidget_gets_the_indexed_keys_it_reads(self):
        fields = {"pair": PairField()}
        value = {"left": "L", "right": "R"}
        encoded = as_widget_data(fields, {"pair": value})

        self.assertEqual(encoded.get("pair_0"), "L")
        self.assertEqual(encoded.get("pair_1"), "R")
        self.assertEqual(
            fields["pair"].widget.value_from_datadict(encoded, {}, "pair"), ["L", "R"]
        )

    def test_a_declared_inverse_is_used_where_one_exists(self):
        fields = {"rows": forms.JSONField(widget=DeclaredIndexedWidget())}
        encoded = as_widget_data(fields, {"rows": ["a", "b"]})

        self.assertEqual(encoded.get("rows__0"), "a")
        self.assertEqual(encoded.get("rows__1"), "b")

    def test_a_declared_inverse_is_preferred_over_the_multiwidget_rule(self):
        class DeclaringPairWidget(PairWidget):
            def value_to_datadict(self, name, value):
                return {f"{name}_0": "declared", f"{name}_1": "declared"}

        fields = {"pair": PairField(widget=DeclaringPairWidget())}
        encoded = as_widget_data(fields, {"pair": {"left": "L", "right": "R"}})

        self.assertEqual(encoded.get("pair_0"), "declared")

    def test_a_field_absent_from_the_values_is_not_invented(self):
        encoded = as_widget_data({"pair": PairField()}, {})
        self.assertNotIn("pair_0", encoded)


class UnreadableTest(SimpleTestCase):
    def test_a_widget_that_ignores_the_encoding_is_reported(self):
        fields = {"rows": forms.JSONField(widget=IndexedWidget())}
        values = {"rows": ["a", "b"]}

        findings = unreadable(fields, values, as_widget_data(fields, values))

        self.assertEqual(findings, {"rows": ("IndexedWidget", "ignored")})

    def test_declaring_the_inverse_clears_the_report(self):
        fields = {"rows": forms.JSONField(widget=DeclaredIndexedWidget())}
        values = {"rows": ["a", "b"]}

        self.assertEqual(unreadable(fields, values, as_widget_data(fields, values)), {})

    def test_an_unchecked_checkbox_is_not_reported(self):
        # False and "nothing posted" are the same submission for a checkbox, so
        # the widget answering False is the right answer, not a lost value.
        fields = {"flag": forms.BooleanField(required=False)}
        values = {"flag": False}

        self.assertEqual(unreadable(fields, values, as_widget_data(fields, values)), {})

    def test_a_checked_checkbox_is_not_reported(self):
        fields = {"flag": forms.BooleanField(required=False)}
        values = {"flag": True}

        self.assertEqual(unreadable(fields, values, as_widget_data(fields, values)), {})

    def test_a_multiwidget_whose_parts_are_all_empty_is_not_reported(self):
        # The regression this comparison replaced a heuristic for: the widget
        # read {"left": "", "right": ""} perfectly, into ["", ""]. Judging the
        # decoded value for emptiness called that a lost value and refused a
        # write that was entirely correct.
        fields = {"pair": PairField()}
        values = {"pair": {"left": "", "right": ""}}

        self.assertEqual(unreadable(fields, values, as_widget_data(fields, values)), {})

    def test_a_widget_that_raises_is_reported_as_an_error(self):
        fields = {"boom": forms.CharField(widget=ExplodingWidget())}
        values = {"boom": "x"}

        self.assertEqual(
            unreadable(fields, values, as_widget_data(fields, values)),
            {"boom": ("ExplodingWidget", "error")},
        )

    def test_nothing_posted_has_nothing_to_report(self):
        fields = {"rows": forms.JSONField(widget=IndexedWidget())}
        for value in (None, []):
            with self.subTest(value=value):
                values = {"rows": value}
                self.assertEqual(
                    unreadable(fields, values, as_widget_data(fields, values)), {}
                )

    def test_declared_inverse_is_sound_agrees_with_unreadable(self):
        # The contract a package can assert for itself. A widget that passes
        # here cannot be reported there, and one that fails here will be.
        self.assertTrue(
            declared_inverse_is_sound(DeclaredIndexedWidget(), "rows", ["a"])
        )
        self.assertFalse(declared_inverse_is_sound(IndexedWidget(), "rows", ["a"]))

    def test_a_declared_inverse_that_encodes_nothing_is_unsound(self):
        class LyingWidget(IndexedWidget):
            def value_to_datadict(self, name, value):
                return {}

        self.assertFalse(declared_inverse_is_sound(LyingWidget(), "rows", ["a"]))


class RefuseUnreadableTest(SimpleTestCase):
    def setUp(self):
        self.fields = {"rows": forms.JSONField(widget=IndexedWidget())}

    def _encoded(self, values):
        return as_widget_data(self.fields, values)

    def test_a_supplied_value_is_refused_as_the_callers_own(self):
        supplied = {"rows": ["a"]}

        with self.assertRaises(ValidationError) as caught:
            refuse_unreadable(self.fields, supplied, {}, self._encoded(supplied))

        message = caught.exception.message_dict["rows"][0]
        self.assertIn("A value was supplied", message)
        self.assertIn("IndexedWidget", message)

    def test_a_stored_value_is_refused_as_data_a_partial_change_would_lose(self):
        stored = {"rows": ["a"]}

        with self.assertRaises(ValidationError) as caught:
            refuse_unreadable(self.fields, {}, stored, self._encoded(stored))

        message = caught.exception.message_dict["rows"][0]
        self.assertIn("already holds a value", message)

    def test_a_stored_value_the_caller_is_replacing_is_not_refused_twice(self):
        # The caller sent this field, so its stored value is going away either
        # way: only the supplied sentence applies.
        supplied = stored = {"rows": ["a"]}

        with self.assertRaises(ValidationError) as caught:
            refuse_unreadable(self.fields, supplied, stored, self._encoded(stored))

        self.assertEqual(len(caught.exception.message_dict["rows"]), 1)

    def test_an_empty_stored_value_has_nothing_to_lose(self):
        refuse_unreadable(self.fields, {}, {"rows": None}, self._encoded({"rows": None}))

    def test_nothing_unreadable_raises_nothing(self):
        fields = {"name": forms.CharField()}
        values = {"name": "Lizzie"}
        refuse_unreadable(fields, values, {}, as_widget_data(fields, values))


class CleanPluginDataTest(CMSTestCase):
    """The step between a caller's ``data`` and the plugin's bound form."""

    def setUp(self):
        page = create_page("home", "nav_playground.html", "en")
        self.placeholder = page.get_placeholders("en").get(slot="body")
        self.link = add_plugin(
            self.placeholder,
            "LinkPlugin",
            "en",
            name="Original",
            external_link="https://example.com/original",
        )

    def _clean(self, data, instance=None):
        return LinkPlugin.clean_plugin_data(self.placeholder.source, data, instance=instance)

    # -- widget-shaped input -------------------------------------------------
    def test_a_composite_widgets_value_reaches_its_field(self):
        class PairForm(forms.ModelForm):
            name = PairField()

            class Meta:
                model = Link
                fields = ["name", "external_link"]

            def clean_name(self):
                pair = self.cleaned_data["name"]
                return f"{pair['left']}/{pair['right']}"

        with patch.object(LinkPlugin, "form", PairForm):
            form = self._clean(
                {
                    "name": {"left": "L", "right": "R"},
                    "external_link": "https://example.com/",
                }
            )

        self.assertEqual(form.cleaned_data["name"], "L/R")

    def test_a_value_no_widget_reads_is_refused_rather_than_dropped(self):
        class IgnoringForm(forms.ModelForm):
            name = forms.CharField(widget=IndexedWidget())

            class Meta:
                model = Link
                fields = ["name", "external_link"]

        with patch.object(LinkPlugin, "form", IgnoringForm):
            with self.assertRaises(ValidationError) as caught:
                self._clean(
                    {"name": "Lizzie", "external_link": "https://example.com/"}
                )

        self.assertIn("IndexedWidget", caught.exception.message_dict["name"][0])
