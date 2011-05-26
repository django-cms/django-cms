from django.core.management.base import LabelCommand, CommandError
from cms.models.titlemodels import Title

class Command(LabelCommand):
    
    args = "APPHOK_NAME"
    label = 'apphook name (SampleApp)'
    help = 'Uninstalls specified apphooks from the Title model (Pages)'
    
    def handle_label(self, label, **options):
        queryset = Title.objects.filter(application_urls=label)
        number_of_apphooks = queryset.count()
        
        if number_of_apphooks > 0:
            queryset.update(application_urls=None)
            print '%d "%s" apphooks uninstalled' % (number_of_apphooks, label)
        else:
            print 'no "%s" apphooks found' % label