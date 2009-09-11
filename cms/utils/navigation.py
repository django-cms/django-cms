from cms import settings 

class NavigationNode(object):
    def __init__(self, title, url):
        self.title = title
        self.url = url
    def get_title(self):
        return self.title
    def get_menu_title(self):
        return self.title
    def get_absolute_url(self):
        return self.url
    childrens = []

def handle_navigation_manipulators(navigation_tree, request):
    for handler_function_name, name in settings.CMS_NAVIGATION_MODIFIERS:
        func_name = handler_function_name.split(".")[-1]
        modifier = __import__(".".join(handler_function_name.split(".")[:-1]),(),(),(func_name,))
        handler_func = getattr(modifier, func_name)  
        handler_func(navigation_tree, request)
    return navigation_tree