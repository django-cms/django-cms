# Create your views here.
from django.shortcuts import render_to_response
from django.template.context import RequestContext

def sample_view(request, **kw):
    context = RequestContext(request, kw)
    return render_to_response("sampleapp/home.html", context)
