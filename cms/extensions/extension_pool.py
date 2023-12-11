from cms.exceptions import SubClassNeededError

from .models import PageContentExtension, PageExtension


class ExtensionPool:
    def __init__(self):
        self.page_extensions = set()
        self.page_content_extensions = set()

    def register(self, extension):
        """
        Registers the given extension.

        Example::

            class MyExtension(PageExtension):
                pass

            extension_pool.register(MyExtension)

        or as decorator::

            @extension_pool.register
            class MyExtension(PageExtension):
                pass

        """

        if issubclass(extension, PageExtension):
            self.page_extensions.add(extension)
        elif issubclass(extension, PageContentExtension):
            self.page_content_extensions.add(extension)
        else:
            raise SubClassNeededError(
                f'Extension has to subclass either {PageExtension} or {PageContentExtension}. {extension} does not!'
            )
        return extension

    def unregister(self, extension):
        """
        Unregisters the given extension. No error is thrown if given extension isn't an extension or wasn't
        registered yet.
        """

        try:
            if issubclass(extension, PageExtension):
                self.page_extensions.remove(extension)
            elif issubclass(extension, PageContentExtension):
                self.page_content_extensions.remove(extension)
        except KeyError:
            pass

    def _copy_page_extensions(self, source_page, target_page, language):
        for extension in self.page_extensions:
            for instance in extension.objects.filter(extended_object=source_page):
                instance.copy(target_page, language)

    def _copy_content_extensions(self, source_page, target_page, language):
        source_content = source_page.pagecontent_set(manager="admin_manager").current_content(language=language).get()
        target_content = target_page.pagecontent_set(manager="admin_manager").current_content(language=language).get()
        for extension in self.page_content_extensions:
            for instance in extension.objects.filter(extended_object=source_content):
                instance.copy(target_content, language)

    def copy_extensions(self, source_page, target_page, languages=None):
        if not languages:
            languages = target_page.get_languages()
        if self.page_extensions:
            self._copy_page_extensions(source_page, target_page, None)
        for language in languages:
            if self.page_content_extensions:
                self._copy_content_extensions(source_page, target_page, language)

    def get_page_extensions(self, page=None):
        extensions = []
        for extension in self.page_extensions:
            if page:
                extensions.extend(list(extension.objects.filter(extended_object=page)))
            else:
                extensions.extend(list(extension.objects.all()))
        return extensions

    def get_page_content_extensions(self, page_content=None):
        extensions = []
        for extension in self.page_content_extensions:
            if page_content:
                extensions.extend(list(extension.objects.filter(extended_object=page_content)))
            else:
                extensions.extend(list(extension.objects.all()))
        return extensions


extension_pool = ExtensionPool()
