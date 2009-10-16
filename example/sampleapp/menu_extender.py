from cms.utils.navigation import NavigationNode
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

def get_nodes(request):
    res = [] # result list
    n = NavigationNode(_('Sublevel'), reverse('sample-app-sublevel'))
    n2 = NavigationNode(_('Sublevel3'), reverse('sample-app-sublevel3'))
    n.childrens = [n2]
    res.append(n)
    n = NavigationNode(_('Sublevel 2'), reverse('sample-app-sublevel2'))
    res.append(n)
    return res
