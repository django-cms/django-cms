from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from . import views

"""
Also used in cms.tests.ApphooksTestCase
"""
urlpatterns = [
    path('', views.sample_view, {'message': 'sample root page',}, name='sample-root'),
    path('exempt/', views.exempt_view, {'message': 'sample root page',}, name='sample-exempt'),
    path('settings/', views.sample_view, kwargs={'message': 'sample settings page'}, name='sample-settings'),
    re_path(r'^myparams/(?P<my_params>[\w_-]+)/$', views.sample_view, name='sample-params'),
    re_path(_(r'^account/$'), views.sample_view, {'message': 'sample account page'}, name='sample-account'),
    path('account/my_profile/',views.sample_view, {'message': 'sample my profile page'}, name='sample-profile'),
    path('category/<int:id>/', views.category_view, name='category_view'),
    path('notfound/', views.notfound, name='notfound'),
    path('extra_1/', views.extra_view, {'message': 'test urlconf'}, name='extra_first'),
    path('class-view/', views.ClassView(), name='sample-class-view'),
    path('class-based-view/', views.ClassBasedView.as_view(), name='sample-class-based-view'),
    path('', include('cms.test_utils.project.sampleapp.urls_extra'), {'opts': 'someopts'}),
]
