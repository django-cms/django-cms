from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0042_remove_placeholderreference_placeholder_ref_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="globalpagepermission",
            name="can_change_permissions",
            field=models.BooleanField(
                default=False,
                help_text=_("Allows granting and revoking permissions for this page covered by this permission."),
                verbose_name=_("can change permissions"),
            ),
        ),
        migrations.AlterField(
            model_name="pagepermission",
            name="can_change_permissions",
            field=models.BooleanField(
                default=False,
                help_text=_("Allows granting and revoking permissions for this page covered by this permission."),
                verbose_name=_("can change permissions"),
            ),
        ),
        migrations.AlterField(
            model_name="globalpagepermission",
            name="can_view",
            field=models.BooleanField(
                default=False,
                help_text=_(
                    "Grants frontend view access. Note: as soon as any user or "
                    "group is given view access to a page, that page becomes "
                    "restricted — only users/groups with view access can then "
                    "see it on the frontend."
                ),
                verbose_name=_("can view restricted pages"),
            ),
        ),
        migrations.AlterField(
            model_name="pagepermission",
            name="can_view",
            field=models.BooleanField(
                default=False,
                help_text=_(
                    "Grants frontend view access. Note: as soon as any user or "
                    "group is given view access to a page, that page becomes "
                    "restricted — only users/groups with view access can then "
                    "see it on the frontend."
                ),
                verbose_name=_("can view restricted pages"),
            ),
        ),
    ]
