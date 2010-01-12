class ViewNameMiddleware(object):  
    def process_view(self, request, view_func, view_args, view_kwargs):  
        """ 
        get the current view and its args so we maybe can do a reverse on 
        it with a different language namespace
        """
        request.view_name = ".".join((view_func.__module__, view_func.__name__))
        print request.view_name
        print view_args
        print view_kwargs  
        