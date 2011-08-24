from django.shortcuts import render_to_response
from django.template.context import RequestContext
from project.placeholderapp.models import Example1


def example_view(request):
    context = RequestContext(request)
    context['examples'] = Example1.objects.all()
    return render_to_response('placeholderapp.html', context)
