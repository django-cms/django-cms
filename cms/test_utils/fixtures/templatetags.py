from cms.api import create_page, create_page_content


class TwoPagesFixture:
    def create_fixtures(self):
        defaults = {
            'template': 'nav_playground.html',
            'in_navigation': True,
        }
        with self.settings(CMS_PERMISSION=False):
            first = create_page('first', language='en', **defaults)
            create_page_content('de', 'erste', first)
            second = create_page('second', language='en', reverse_id='myreverseid', **defaults)
            create_page_content('de', 'zweite', second)
