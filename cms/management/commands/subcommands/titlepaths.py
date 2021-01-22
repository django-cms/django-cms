from cms.models import CMSPlugin, TreeNode, Title, Page

from .base import SubcommandsCommand

class CheckTitlePathsCommand(SubcommandsCommand):
    help_string = 'Check page title paths'
    command_name = 'check-title-paths'

    def add_arguments(self, parser):
        parser.add_argument('--fix-paths', action='store_true', required=False,
                            help='Fix title paths (please, save database before doing this!)')

    
    def handle(self, *args, **options):
        self.fix = options.get('fix-paths', False)
        self.checked = not options.get('interactive', True)
            
        root_nodes = TreeNode.objects.filter(parent__isnull=True)

        for node in root_nodes.order_by('site__pk', 'path'):
            # print("node = ", ' ', node.path, ' ', node.site)
            page = node.get_item()
            domain = node.site.domain
            self._check_title_path_recursive(domain, page)
            
    def _check_title_path_recursive(self, domain, page):
        parent_page = page.get_parent_page()
        for language in page.get_languages():
            if parent_page:
                base = parent_page.get_path(language, fallback=True)
            else:
                base = ''
            title_obj = page.get_title_obj(language, fallback=False)
            p1 = title_obj.path
            p2 = title_obj.get_path_for_base(base)
            if p1 != p2:
                print()
                print(domain + '/' + language + '/' + p1)
                print(domain + '/' + language + '/' + p2)
                if self.fix:
                    if self.checked:
                        ok = True
                    else:
                        confirm = input("""
You have requested to change this title path.
Are you sure you want to do this?
Type 'yes' or to continue for this, 'all' to change all title paths, or 'none' to cancel: """)
                        if confirm == 'all':
                            self.checked = True
                            ok = True
                        elif confirm == 'yes':
                            ok = True
                        elif confirm == 'none':
                            self.fix = False
                            ok = False
                        else:
                            ok = False
                    if ok:
                        title_obj.path = p2
                        title_obj.save()
                        print('-> Fixed')
        for p in page.get_child_pages():
            self._check_title_path_recursive(domain, p)

