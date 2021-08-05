from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0015_auto_20160421_0000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aliaspluginmodel',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='cms_aliasplugin', primary_key=True, serialize=False, to='cms.CMSPlugin', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='placeholderreference',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='cms_placeholderreference', primary_key=True, serialize=False, to='cms.CMSPlugin', on_delete=models.CASCADE),
        ),
    ]
