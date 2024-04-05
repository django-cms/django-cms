from cms.api import create_page


class MenusFixture:
    def create_fixtures(self):
        """
        Tree from fixture:

            + P1
            | + P2
            |   + P3
            + P4
            | + P5
            + P6 (not in menu)
              + P7
              + P8
        """
        defaults = {
            'template': 'nav_playground.html',
            'language': 'en',
        }
        with self.settings(CMS_PERMISSION=False):
            p1 = create_page('P1', in_navigation=True, **defaults)
            p1.set_as_homepage()
            p4 = create_page('P4', in_navigation=True, **defaults)
            p6 = create_page('P6', in_navigation=False, **defaults)
            p2 = create_page('P2', in_navigation=True, parent=p1, **defaults)
            create_page('P3', in_navigation=True, parent=p2, **defaults)
            create_page('P5', in_navigation=True, parent=p4, **defaults)
            create_page('P7', in_navigation=True, parent=p6, **defaults)
            create_page('P8', in_navigation=True, parent=p6, **defaults)


class ExtendedMenusFixture:
    def create_fixtures(self):
        """
        Tree from fixture:

            + P1
            | + P2
            |   + P3
            | + P9
            |   + P10
            |      + P11
            + P4
            | + P5
            + P6 (not in menu)
              + P7
              + P8
        """
        defaults = {
            'template': 'nav_playground.html',
            'language': 'en',
        }
        with self.settings(CMS_MODERATOR=False, CMS_PERMISSION=False):
            p1 = create_page('P1', in_navigation=True, **defaults)
            p1.set_as_homepage()
            p4 = create_page('P4', in_navigation=True, **defaults)
            p6 = create_page('P6', in_navigation=False, **defaults)
            p2 = create_page('P2', in_navigation=True, parent=p1, **defaults)
            create_page('P3', in_navigation=True, parent=p2, **defaults)
            create_page('P5', in_navigation=True, parent=p4, **defaults)
            create_page('P7', in_navigation=True, parent=p6, **defaults)
            create_page('P8', in_navigation=True, parent=p6, **defaults)
            p9 = create_page('P9', in_navigation=True, parent=p1, **defaults)
            p10 = create_page('P10', in_navigation=True, parent=p9, **defaults)
            create_page('P11', in_navigation=True, parent=p10, **defaults)


class SubMenusFixture:
    def create_fixtures(self):
        """
        Tree from fixture:

            + P1
            | + P2
            |   + P3
            + P4
            | + P5
            + P6
              + P7 (not in menu)
              + P8
        """
        defaults = {
            'template': 'nav_playground.html',
            'language': 'en',
        }
        with self.settings(CMS_PERMISSION=False):
            p1 = create_page('P1', in_navigation=True, **defaults)
            p1.set_as_homepage()
            p4 = create_page('P4', in_navigation=True, **defaults)
            p6 = create_page('P6', in_navigation=True, **defaults)
            p2 = create_page('P2', in_navigation=True, parent=p1, **defaults)
            create_page('P3', in_navigation=True, parent=p2, **defaults)
            create_page('P5', in_navigation=True, parent=p4, **defaults)
            create_page('P7', in_navigation=False, parent=p6, **defaults)
            create_page('P8', in_navigation=True, parent=p6, **defaults)


class SoftrootFixture:
    def create_fixtures(self):
        """
        top
            root
                aaa
                    111
                        ccc
                            ddd
                    222
                bbb
                    333
                    444

        # all in nav, published and NOT softroot
        """
        defaults = {
            'template': 'nav_playground.html',
            'language': 'en',
            'in_navigation': True,
        }
        with self.settings(CMS_PERMISSION=False):
            top = create_page('top', **defaults)
            top.set_as_homepage()
            root = create_page('root', parent=top, **defaults)
            aaa = create_page('aaa', parent=root, **defaults)
            _111 = create_page('111', parent=aaa, **defaults)
            ccc = create_page('ccc', parent=_111, **defaults)
            create_page('ddd', parent=ccc, **defaults)
            create_page('222', parent=aaa, **defaults)
            bbb = create_page('bbb', parent=root, **defaults)
            create_page('333', parent=bbb, **defaults)
            create_page('444', parent=bbb, **defaults)
