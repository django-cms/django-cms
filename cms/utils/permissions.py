from cms.models import Page

def has_page_add_permission(request, page=None):
    """Return true if the current user has permission to add a new page.
    """        
    permissions = Page.permissions.get_edit_id_list(request.user)
    if permissions is Page.permissions.GRANT_ALL:
        return True
    target = request.GET.get('target', -1)
    position = request.GET.get('position', None)
    if int(target) in permissions:
        if position == "first-child":
            return True
        else:
            if Page.objects.get(pk=target).parent_id in permissions:
                return True
    return False
