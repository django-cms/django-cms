from django.http import Http404
from django.shortcuts import render

from cms.toolbar.utils import get_toolbar_from_request

from .models import FancyPoll


def detail(request, poll_id):
    try:
        poll = FancyPoll.objects.get(pk=poll_id)
    except FancyPoll.DoesNotExist:
        raise Http404('Fancy Poll doesn\'t exist')

    toolbar = get_toolbar_from_request(request)
    toolbar.set_object(poll)
    return render(request, poll.template, {'poll': poll})
