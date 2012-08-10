from cms.utils.helpers import reversion_register
from django.db import models

class FileModel(models.Model):
    test_file = models.FileField(upload_to='fileapp/', blank=True, null=True)

reversion_register(FileModel)
