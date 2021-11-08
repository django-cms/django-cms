from django.urls import include, re_path
from django.utils.translation import gettext_lazy as _

from . import views

"""
Also used in cms.tests.ApphooksTestCase
"""
urlpatterns = [
    re_path(r'^$', views.sample_view, {'message': 'sample root page',}, name='sample-root'),
    re_path(r'^exempt/$', views.exempt_view, {'message': 'sample root page',}, name='sample-exempt'),
    re_path(r'^settings/$', views.sample_view, kwargs={'message': 'sample settings page'}, name='sample-settings'),
    re_path(r'^myparams/(?P<my_params>[\w_-]+)/$', views.sample_view, name='sample-params'),
    re_path(_(r'^account/$'), views.sample_view, {'message': 'sample account page'}, name='sample-account'),
    re_path(r'^account/my_profile/$',views.sample_view, {'message': 'sample my profile page'}, name='sample-profile'),
    re_path(r'^category/(?P<id>[0-9]+)/$', views.category_view, name='category_view'),
    re_path(r'^notfound/$', views.notfound, name='notfound'),
    re_path(r'^extra_1/$', views.extra_view, {'message': 'test urlconf'}, name='extra_first'),
    re_path(r'^class-view/$', views.ClassView(), name='sample-class-view'),
    re_path(r'^class-based-view/$', views.ClassBasedView.as_view(), name='sample-class-based-view'),
    re_path(r'^', include('cms.test_utils.project.sampleapp.urls_extra'), {'opts': 'someopts'}),
]
