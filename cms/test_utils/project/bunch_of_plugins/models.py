from cms.models import CMSPlugin


class TestPlugin1(CMSPlugin):
    pass


class LeftMixin: pass

class RightMixin: pass


class TestPlugin2(LeftMixin, CMSPlugin, RightMixin):
    pass
