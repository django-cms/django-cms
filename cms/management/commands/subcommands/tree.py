from collections import OrderedDict

from django.db import IntegrityError

from cms.models.pagemodel import Page, PageUrl

from .base import SubcommandsCommand


def get_descendants(root):
    """
    Returns a generator of primary keys which represent
    descendants of the given node ID (root_id)
    """
    # Note this is done because get_descendants() can't be trusted
    # as the tree can be corrupt.
    children = Page.objects.filter(parent=root).order_by('path')

    for child in children.iterator():
        yield child

        yield from get_descendants(child)


class FixTreeCommand(SubcommandsCommand):
    help_string = 'Repairing Materialized Path Tree for Pages'
    command_name = 'fix-tree'

    def handle(self, *args, **options):
        """
        Repairs the tree
        """
        self.stdout.write('fixing page tree')
        Page.fix_tree()

        root_pages = Page.objects.filter(parent__isnull=True)

        last = None

        try:
            first = root_pages.order_by('path').first()
        except IndexError:
            first = None

        for page in root_pages.order_by('site__pk', 'path'):
            if last:
                last.refresh_from_db()
                page.refresh_from_db()
                page.move(target=last, pos='right')
            elif first and first.pk != page.pk:
                page.move(target=first, pos='left')
            last = page

        for root in root_pages.order_by('site__pk', 'path'):
            self._update_descendants_tree(root)

        self.stdout.write('fixing page URLs')
        for page in root_pages:
            for language in page.get_languages():
                if not page.is_home:
                    page._update_url_path(language)
                self._update_url_path_recursive(page, language)

        self.stdout.write('all done')

    def _update_descendants_tree(self, root):
        pages = Page.objects.all()
        descendants_by_parent = OrderedDict()

        for descendant in get_descendants(root):
            parent_id = descendant.parent_id
            descendants_by_parent.setdefault(parent_id, []).append(descendant)

        for tree in descendants_by_parent.values():
            last_page = None

            for page in tree:
                page.refresh_from_db()

                if last_page:
                    # This is not the first loop so this is not the first draft
                    # child. Set this page a sibling of the last processed
                    # draft page.
                    last_page.refresh_from_db()
                    page.move(target=last_page, pos='right')
                else:
                    # This is the first time through the loop so this is the first
                    # draft child for this parent.
                    page.move(target=pages.get(pk=tree[0].parent_id), pos='first-child')
                last_page = page

    def _update_url_path_recursive(self, page, language):
        if page.node.is_leaf() or language not in page.get_languages():
            return

        pages = page.get_child_pages()
        base_path = page.get_path(language)
        new_path = page._get_path_sql_value(base_path)

        try:
            (PageUrl
             .objects
             .filter(language=language, page__in=pages)
             .exclude(managed=False)
             .update(path=new_path))
        except IntegrityError as exc:
            self.stdout.write(f"{exc} while updating path for page: /{language}/{new_path}")

        for child in pages.filter(urls__language=language).iterator():
            self._update_url_path_recursive(child, language)
