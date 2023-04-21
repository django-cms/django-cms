def wo_content_permission(method):
    """Decorator to temporarily switch of write permissions to content"""
    def inner(self, *args, **kwargs):
        self.admin.change_content = False
        try:
            return_value = method(self, *args, **kwargs)
        except Exception:
            raise
        finally:
            self.admin.change_content = True
        return return_value
    return inner
