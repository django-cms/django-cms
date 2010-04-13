from django.db import models
from cms.models.fields import PlaceholderField


class BlogPost(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User')
    contents = PlaceholderField('blogpost')
