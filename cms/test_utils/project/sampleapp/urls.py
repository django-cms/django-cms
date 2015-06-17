from django.conf.urls import url, include
from django.utils.translation import ugettext_lazy as _

from . import views

"""
Also used in cms.tests.ApphooksTestCase
"""
urlpatterns = [
    url(r'^$', views.sample_view, {'message': 'sample root page',}, name='sample-root'),
    url(r'^exempt/$', views.exempt_view, {'message': 'sample root page',}, name='sample-exempt'),
    url(r'^settings/$', views.sample_view, kwargs={'message': 'sample settings page'}, name='sample-settings'),
    url(r'^myparams/(?P<my_params>[\w_-]+)/$', views.sample_view, name='sample-params'),
    url(_(r'^account/$'), views.sample_view, {'message': 'sample account page'}, name='sample-account'),
    url(r'^account/my_profile/$',views.sample_view, {'message': 'sample my profile page'}, name='sample-profile'),
    url(r'^category/(?P<id>[0-9]+)/$', views.category_view, name='category_view'),
    url(r'^notfound/$', views.notfound, name='notfound'),
    url(r'^extra_1/$', views.extra_view, {'message': 'test urlconf'}, name='extra_first'),
    url(r'^class-view/$', views.ClassView(), name='sample-class-view'),
    url(r'^class-based-view/$', views.ClassBasedView.as_view(), name='sample-class-based-view'),
    url(r'^', include('cms.test_utils.project.sampleapp.urls_extra'), {'opts': 'someopts'}),
]
