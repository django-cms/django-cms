import aldryn_addons.urls
from aldryn_django.utils import i18n_patterns

urlpatterns = (
    [
        # add your own patterns here
    ]
    + aldryn_addons.urls.patterns()
    + i18n_patterns(
        # add your own i18n patterns here
        *aldryn_addons.urls.i18n_patterns()  # MUST be the last entry!
    )
)
