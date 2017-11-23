from django import forms

from cms.models import CMSPlugin


class MultiWrapForm(forms.ModelForm):
    NUM_WRAPS = (
        (0, "0"),
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
        (6, "6"),
        (7, "7"),
        (8, "8"),
        (9, "9"),
        (10, "10"),
    )

    create = forms.ChoiceField(
        choices=NUM_WRAPS,
        label="Create Wraps",
        help_text="Create this number of wraps"
    )

    class Meta:
        model = CMSPlugin
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
