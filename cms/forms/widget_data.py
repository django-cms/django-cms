"""Form input in the shape each field's widget actually reads.

Django's widget protocol is **decode-only**. ``Form(data=...)`` expects the
flat, stringly mapping an HTML POST produces, and every widget turns that back
into a Python value through ``value_from_datadict``. There is no inverse in
Django, because a browser never needs one: the widget renders the keys, and the
browser posts them back.

A caller that has no browser -- :meth:`CMSPluginBase.clean_plugin_data
<cms.core.plugin_base.CMSPluginBase.clean_plugin_data>`, and so every caller of
:mod:`cms.core.services` that passes ``data`` instead of a form -- does need
one. A composite widget does not read ``data[name]`` at all; it reads the
several keys its own template emits:

* a :class:`~django.forms.widgets.MultiWidget` reads ``name_0``, ``name_1``...
* ``djangocms_attributes_field``'s ``AttributesWidget`` reads
  ``attributes_key[name]`` and ``attributes_value[name]``, as parallel lists.

So a caller that passes ``{"attributes": {"data-x": "1"}}`` -- the obvious
thing -- has its value **silently discarded**: ``value_from_datadict`` returns
``{}``, the form still reports ``is_valid()``, and the write succeeds having
lost the field.

This module closes that by writing, beside the caller's own value, the keys the
widget reads. Three rules decide how, in order, and none of them is knowledge
of a particular plugin:

1. ``widget.value_to_datadict(name, value)``, if the widget declares it. This
   is the **published inverse**: a widget with a protocol of its own invention
   declares how to encode it, next to the ``value_from_datadict`` that decodes
   it, where the two cannot drift apart. See :func:`declared_inverse_is_sound`
   for the contract it has to satisfy.
2. ``MultiWidget.decompress(value)``, which is the exact inverse of what
   ``value_from_datadict`` reassembles -- so every MultiWidget, including ones
   nobody here has seen, is handled by Django's own API.
3. The attributes key/value protocol, which predates this module's hook and
   belongs to a package that cannot be asked to grow one, so it gets a single
   declared encoder applied only where the package is installed.

Two properties worth stating, because they are what make this safe:

* It is **additive**. The caller's ``name: value`` entries are kept, so every
  widget that already read plain data behaves exactly as before.
* It returns a :class:`~django.utils.datastructures.MultiValueDict`, **not** a
  :class:`~django.http.QueryDict`. A QueryDict coerces everything to a string,
  which would turn a dict bound for a ``JSONField`` into a Python ``repr`` and
  be refused as "Value must be valid JSON". A MultiValueDict provides the
  ``getlist`` widgets need while leaving values untouched.

What cannot be encoded is **refused, not dropped**: :func:`unreadable` reports
every value that did not reach its field, naming the field and the widget
class. A widget this module has never heard of therefore produces a loud
refusal rather than a silent write, which is the whole point -- the failure it
replaces reported success.
"""

from __future__ import annotations

from collections.abc import Mapping

from django.forms.widgets import MultiWidget
from django.utils.datastructures import MultiValueDict

__all__ = [
    "as_widget_data",
    "declared_inverse_is_sound",
    "encoder_for",
    "posted_values",
    "refuse_unreadable",
    "unreadable",
]


def _attributes_widget():
    """``AttributesWidget``, or ``None`` where the package is not installed.

    An optional dependency: the CMS does not require
    ``djangocms-attributes-field``, and a deployment without it has no such
    field to encode.
    """
    try:
        from djangocms_attributes_field.widgets import AttributesWidget
    except ImportError:
        return None
    return AttributesWidget


def _encode_declared(widget, name, value, out):
    """Whatever the widget says its own input looks like.

    The widget returns a mapping of flat key to value, or to a list of values
    where it reads a list. Anything else is a broken declaration and is left
    for :func:`unreadable` to report, rather than written half-way.
    """
    encoded = widget.value_to_datadict(name, value)
    if not isinstance(encoded, Mapping):
        return False
    for key, part in encoded.items():
        out.setlist(key, list(part) if isinstance(part, (list, tuple)) else [part])
    return True


def _encode_multiwidget(widget, name, value, out):
    """``name_0``, ``name_1``... from the widget's own ``decompress``."""
    for index, part in enumerate(widget.decompress(value)):
        out.setlist(f"{name}_{index}", [part])
    return True


def _encode_attributes(widget, name, value, out):
    """``attributes_key[name]`` / ``attributes_value[name]``, as parallel lists.

    Insertion order is preserved on both sides, which is what the widget zips
    back together. A non-dict is left alone for the field to refuse, rather
    than coerced into one here.
    """
    if not isinstance(value, dict):
        return False
    out.setlist(f"attributes_key[{name}]", list(value.keys()))
    out.setlist(f"attributes_value[{name}]", [str(item) for item in value.values()])
    return True


def encoder_for(widget):
    """The encoder for *widget*, or ``None`` if it reads plain data already.

    Order matters: a widget that declares its own inverse is believed over any
    rule inferred from its class, including the MultiWidget one. That is what
    lets a MultiWidget subclass whose ``value_from_datadict`` does something
    other than reassemble its parts say so.
    """
    if widget is None:
        return None
    if callable(getattr(widget, "value_to_datadict", None)):
        return _encode_declared
    if isinstance(widget, MultiWidget):
        return _encode_multiwidget
    attributes = _attributes_widget()
    if attributes is not None and isinstance(widget, attributes):
        return _encode_attributes
    return None


def posted_values(field, value):
    """*value* as the list of values posted under its own key.

    Three distinctions a browser makes for free and a Python caller does not:

    * ``None`` is **nothing posted**, not the value ``None``. A widget that
      asks for ``getlist`` would otherwise be handed ``[None]`` and clean it as
      a choice called "None" -- which is how a cleared multi-select came back
      as *"Select a valid choice. None is not one of the available choices."*
    * ``""`` is nothing for a field that takes several values, because an empty
      multi-select posts no keys at all rather than one empty one. For every
      other field it is a real empty submission, so the question is asked of
      the field, not of the value.
    * A **list** is several posted values for a field that takes several, and
      one value that merely happens to be a list for a field that does not --
      a ``JSONField`` holding an array, say. Spreading it either way would hand
      a JSONField the array's last element.

    The signal is ``widget.allow_multiple_selected``, Django's own, and the
    widget is the right authority because the widget is what reads the data.
    Measured against every field of all 135 installed plugin types: it agrees
    with the field's own class (``MultipleChoiceField`` and friends) in every
    case, so there is nothing to be gained by consulting both.

    One deliberate limit, and it is Django's rather than a choice made here:
    :meth:`MultiValueDict.get
    <django.utils.datastructures.MultiValueDict.get>` returns its *default*
    when the stored value is ``[]``, so a scalar field cannot be handed an
    empty list -- ``[[]]`` would satisfy ``getlist`` and read back as ``None``
    through ``get``. An empty list is therefore nothing posted for a scalar
    field too. The quirk never fires for a real submission, where a present key
    always carries at least one value; it fires here only for the empty list we
    write to mean "nothing", which is exactly when returning the default is
    right.
    """
    if value is None:
        return []
    several = bool(getattr(getattr(field, "widget", None),
                           "allow_multiple_selected", False))
    if isinstance(value, (list, tuple)):
        if several:
            return list(value)
        return [value] if value else []
    if value == "" and several:
        return []
    return [value]


def as_widget_data(fields, values):
    """*values*, plus the flattened keys their composite widgets read.

    ``fields`` is a mapping of field name to :class:`~django.forms.Field` --
    ``form.fields`` of an instantiated form rather than ``base_fields``, so
    that a field a form adds in its ``__init__`` is encoded too.

    Additive and non-destructive: see the module docstring for why that
    matters. A value whose encoder raises is left unencoded for
    :func:`unreadable` to report; swallowing the failure and writing the
    default is the behaviour this module exists to remove.
    """
    out = MultiValueDict()
    for name, value in values.items():
        out.setlist(name, posted_values(fields.get(name), value))

    for name, field in fields.items():
        if name not in values:
            continue                      # absent, and not ours to invent
        widget = getattr(field, "widget", None)
        encoder = encoder_for(widget)
        if encoder is None:
            continue
        try:
            encoder(widget, name, values[name], out)
        except Exception:
            continue
    return out


def unreadable(fields, values, encoded):
    """Which of *values* did not reach their field, and why.

    Returns ``{field name: (widget class name, reason)}``, where *reason* is
    ``"ignored"`` when the widget took no notice of the encoding and
    ``"error"`` when asking it raised. Empty when everything landed.

    One rule, and no judgement anywhere about what counts as an empty value.
    Each widget is asked two questions -- what it reads from the encoded data,
    and what it reads from a submission that said **nothing at all** -- and the
    value is reported when the two agree *and* the caller did not supply that
    same answer. Supplying it is not a failure: an unchecked checkbox and an
    absent checkbox are the same submission, so a caller who sends ``False``
    has been read correctly by a widget that answers ``False`` either way.

    A value that encodes to no submission at all (:func:`posted_values`
    returning ``[]`` -- ``None``, or ``""`` for a field taking several values)
    is skipped, because there is nothing for a widget to have ignored.

    Two heuristics stood here before and both were wrong, in opposite
    directions. "Is the decoded value empty?" refused ``TitleWidget``
    decompressing ``{"show": False, "title": ""}`` to ``[False, ""]`` -- a
    value it had read perfectly. "Is the supplied value empty?" let the same
    refusal through for every ``False`` checkbox, because ``False`` is not
    equal to ``""``, ``{}``, ``[]`` or ``None`` and so passed for a value worth
    checking. Comparing against the widget's own no-submission answer needs
    neither question asked.

    A report rather than a refusal, because the two callers phrase it
    differently: one is talking about a value the caller just sent, the other
    about a value already stored that a partial change would silently drop.
    Both are this function's finding; neither sentence belongs to it.
    """
    silent = MultiValueDict()
    findings = {}
    for name, field in fields.items():
        if name not in values or not posted_values(field, values[name]):
            continue
        widget = getattr(field, "widget", None)
        if widget is None:
            continue
        try:
            decoded = widget.value_from_datadict(encoded, {}, name)
            unposted = widget.value_from_datadict(silent, {}, name)
        except Exception:
            findings[name] = (type(widget).__name__, "error")
            continue
        if decoded == unposted and values[name] != unposted:
            findings[name] = (type(widget).__name__, "ignored")
    return findings


def refuse_unreadable(fields, supplied, stored, encoded):
    """Refuse a plugin write whose values would not reach their fields.

    Two findings, kept apart because they are different problems with
    different remedies:

    * a value the **caller supplied** that its widget does not read. The write
      would succeed having lost it.
    * a value **already stored** that cannot be re-encoded. The caller did not
      send this field, so a partial change would re-save the plugin with it
      emptied -- data loss caused by editing something else. Only a populated
      field counts: a stored value that is already empty has nothing to lose.

    Reported together so a caller hears about every field at once, keyed by
    field name exactly like any other form error.

    :raises ~django.core.exceptions.ValidationError: keyed by field name.
    """
    from django.core.exceptions import ValidationError
    from django.utils.translation import gettext as _

    errors = {}
    for name, (widget, reason) in unreadable(fields, supplied, encoded).items():
        if reason == "error":
            errors[name] = [
                _("%(widget)s could not read this value. It is refused rather "
                  "than written as empty.") % {"widget": widget}]
        else:
            errors[name] = [
                _("A value was supplied but %(widget)s does not read it, so it "
                  "would be stored empty. Encode it as that widget's own input, "
                  "or give the widget a value_to_datadict() inverse. The value "
                  "is refused rather than lost.") % {"widget": widget}]

    outstanding = {name: value for name, value in stored.items()
                   if name not in supplied}
    for name, (widget, _reason) in unreadable(fields, outstanding, encoded).items():
        errors.setdefault(name, []).append(
            _("This field already holds a value that %(widget)s cannot read "
              "back, so changing another field would silently empty it. Send "
              "this field explicitly, or give the widget a "
              "value_to_datadict() inverse.") % {"widget": widget})

    if errors:
        raise ValidationError(errors)


def declared_inverse_is_sound(widget, name, value):
    """Whether ``widget``'s declared inverse round-trips *value*.

    The contract a widget takes on by declaring ``value_to_datadict``: what it
    encodes, its own ``value_from_datadict`` must decode back to something
    other than what it reads from a submission that said nothing. Exposed so a
    package can assert it in its own tests rather than discover the mismatch as
    a silently dropped field in production.

    The same comparison :func:`unreadable` makes, deliberately -- a widget that
    passes here cannot be refused there, and one that fails here will be.
    """
    if not callable(getattr(widget, "value_to_datadict", None)):
        return False
    out = MultiValueDict()
    out.setlist(name, [value])
    if not _encode_declared(widget, name, value, out):
        return False
    return (widget.value_from_datadict(out, {}, name)
            != widget.value_from_datadict(MultiValueDict(), {}, name))
