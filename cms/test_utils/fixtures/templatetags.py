from cms.api import create_page, create_title


class TwoPagesFixture:
    def create_fixtures(self):
        defaults = {
            'template': 'nav_playground.html',
            'published': True,
            'in_navigation': True,
        }
        with self.settings(CMS_PERMISSION=False):
            first = create_page('first', language='en', **defaults)
            create_title('de', 'erste', first)
            second = create_page('second', language='en', reverse_id='myreverseid', **defaults)
            create_title('de', 'zweite', second)
