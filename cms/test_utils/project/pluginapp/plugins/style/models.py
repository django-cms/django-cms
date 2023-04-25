from django.db import models

from cms.models import CMSPlugin

CLASS_CHOICES = ['container', 'content', 'teaser']
CLASS_CHOICES = tuple((entry, entry) for entry in CLASS_CHOICES)

TAG_CHOICES = [
    'div', 'article', 'section', 'header', 'footer', 'aside',
     'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
]
TAG_CHOICES = tuple((entry, entry) for entry in TAG_CHOICES)


class Style(CMSPlugin):
    """
    Renders a given ``TAG_CHOICES`` element with additional attributes
    """
    label = models.CharField(
        verbose_name='Label',
        blank=True,
        max_length=255,
        help_text='Overrides the display name in the structure mode.',
    )
    tag_type = models.CharField(
        verbose_name='Tag type',
        choices=TAG_CHOICES,
        default=TAG_CHOICES[0][0],
        max_length=255,
    )
    class_name = models.CharField(
        verbose_name='Class name',
        choices=CLASS_CHOICES,
        default=CLASS_CHOICES[0][0],
        blank=True,
        max_length=255,
    )
    additional_classes = models.CharField(
        verbose_name='Additional classes',
        blank=True,
        max_length=255,
    )

    def __str__(self):
        return self.label or self.tag_type or str(self.pk)

    def get_short_description(self):
        # display format:
        # Style label <tag> .list.of.classes #id
        display = []
        classes = []

        if self.label:
            display.append(self.label)
        if self.tag_type:
            display.append('<{0}>'.format(self.tag_type))
        if self.class_name:
            classes.append(self.class_name)
        if self.additional_classes:
            classes.extend(item.strip() for item in self.additional_classes.split(',') if item.strip())
        display.append('.{0}'.format('.'.join(classes)))
        return ' '.join(display)

    def get_additional_classes(self):
        return ' '.join(item.strip() for item in self.additional_classes.split(',') if item.strip())
