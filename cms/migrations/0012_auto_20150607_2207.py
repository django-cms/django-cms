from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0011_auto_20150419_1006'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalpagepermission',
            name='sites',
            field=models.ManyToManyField(help_text='If none selected, user haves granted permissions to all sites.', to='sites.Site', verbose_name='sites', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='user',
            field=models.OneToOneField(on_delete=models.CASCADE, related_name='djangocms_usersettings', editable=False, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
