from django.conf.urls.defaults import *
from project.placeholderapp.models import *
from django.views.generic.list_detail import object_detail

example1_dict = {
    'queryset': Example1.objects.all(),
}

urlpatterns = patterns('',
    (r'(?P<object_id>\d+)/$', object_detail, example1_dict, 'placeholderapp_example1_detail'),
)