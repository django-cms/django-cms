# -*- coding: utf-8 -*-
from contextlib import contextmanager
import inspect
from itertools import chain

from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.termcolors import colorize
from sekizai.helpers import validate_template

from cms import constants
from cms.models import AliasPluginModel
from cms.utils.conf import get_cms_setting
from cms.utils.compat.dj import is_installed


SUCCESS = 1
WARNING = 2
ERROR = 3
SKIPPED = 4

CHECKERS = []


class FileOutputWrapper(object):
    """
    Wraps two file-like objects (that support at the very least the 'write'
    method) into an API to be used by the check function further down in
    this module.

    The following properties are public (and required) by alternative implementations:

        errors: integer count of errors encountered
        successes: integer count of successes encountered
        warnings: integer count of warnings encountered
        skips: integer count of skips encountered
        successful: Whether the checks were successful (no errors)

    They must also provide these methods:

        write_line(message=''): writes a message to stdout
        write_stderr_line(message=''): writes a message to stderr
        success(message): reports and registers a successful check
        error(message): reports and registers an error
        warn(message); reports and registers a warning
        skip(message): reports and registers a skipped check
        section(title): A context manager that starts a new section. For the
            Section API see FileSectionWrapper
    """
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr
        self.section_wrapper = FileSectionWrapper
        self.errors = 0
        self.successes = 0
        self.warnings = 0
        self.skips = 0

    def colorize(self, msg, opts=(), **kwargs):
        return colorize(msg, opts=opts, **kwargs)

    def write_line(self, message=''):
        self.write(u'%s\n' % message)

    def write(self, message):
        self.stdout.write(message)

    def write_stderr_line(self, message=''):
        self.write_stderr(u'%s\n' % message)

    def write_stderr(self, message):
        self.stderr.write(message)

    def success(self, message):
        self.successes += 1
        self.write_line(u'%s %s' % (message, self.colorize('[OK]', fg='green', opts=['bold'])))

    def error(self, message):
        self.errors += 1
        self.write_stderr_line(u'%s %s' % (message, self.colorize('[ERROR]', fg='red', opts=['bold'])))

    def warn(self, message):
        self.warnings += 1
        self.write_stderr_line(u'%s %s' % (message, self.colorize('[WARNING]', fg='yellow', opts=['bold'])))

    def skip(self, message):
        self.skips += 1
        self.write_line(u'%s %s' % (message, self.colorize('[SKIP]', fg='blue', opts=['bold'])))

    @method_decorator(contextmanager)
    def section(self, title):
        self.write_line(self.colorize(title, opts=['bold']))
        self.write_line(self.colorize('=' * len(title), opts=['bold']))
        self.write_line()
        wrapper = self.section_wrapper(self)
        try:
            yield wrapper
        except:
            self.error('Checker failed, see traceback')
            raise
        self.errors += wrapper.errors
        self.successes += wrapper.successes
        self.warnings += wrapper.warnings
        self.skips += wrapper.skips
        self.write_line('')

    @property
    def successful(self):
        return not self.errors


class FileSectionWrapper(FileOutputWrapper):
    """
    Used from FileOutputWrapper to report checks in a section.

    If you want to provide your own output class, you may want to subclass
    this class for the section reporting too. If you want to use your own,
    you must defined at least the same API as FileOutputWrapper, as well
    as these four additional methods:

        finish_success(message): End the section (successfully)
        finish_error(message): End the section with errors
        finish_warning(message): End this section with a warning
        finish_skip(message): End this (skipped) section
    """
    def __init__(self, wrapper):
        super(FileSectionWrapper, self).__init__(wrapper.stdout, wrapper.stderr)
        self.wrapper = wrapper

    def write_line(self, message=''):
        self.write(u'  - %s\n' % message)

    def write_stderr_line(self, message=''):
        self.write_stderr(u'  - %s\n' % message)

    def finish_success(self, message):
        self.wrapper.write_line()
        self.wrapper.success(message)

    def finish_error(self, message):
        self.wrapper.write_line()
        self.wrapper.error(message)

    def finish_warning(self, message):
        self.wrapper.write_line()
        self.wrapper.warning(message)

    def finish_skip(self, message):
        self.wrapper.write_lin()
        self.wrapper.skip(message)


def define_check(func):
    """
    Helper decorator to register a check function.
    """
    CHECKERS.append(func)
    return func


@define_check
def check_sekizai(output):
    with output.section("Sekizai") as section:
        sekizai_installed = is_installed('sekizai')

        if sekizai_installed:
            section.success("Sekizai is installed")
        else:
            section.error("Sekizai is not installed, could not find 'sekizai' in INSTALLED_APPS")
        processors = list(
            chain(*[template['OPTIONS'].get('context_processors', []) for template in settings.TEMPLATES]))
        if 'sekizai.context_processors.sekizai' in processors:
            section.success("Sekizai template context processor is installed")
        else:
            section.error("Sekizai template context processor is not installed, could not find "
                          "'sekizai.context_processors.sekizai' in TEMPLATES option context_processors")

        if not sekizai_installed:
            # sekizai is not installed.
            # we can't reliable check templates
            # because template loading won't work
            return

        for template, _ in get_cms_setting('TEMPLATES'):
            if template == constants.TEMPLATE_INHERITANCE_MAGIC:
                continue
            if validate_template(template, ['js', 'css']):
                section.success("Sekizai namespaces 'js' and 'css' found in %r" % template)
            else:
                section.error("Sekizai namespaces 'js' and 'css' not found in %r" % template)
        if section.successful:
            section.finish_success("Sekizai configuration okay")
        else:
            section.finish_error("Sekizai configuration has errors")


@define_check
def check_i18n(output):
    with output.section("Internationalization") as section:
        if isinstance(getattr(settings, 'CMS_LANGUAGES', {}), dict):
            section.success("New style CMS_LANGUAGES")
        else:
            section.warn("Old style (tuple based) CMS_LANGUAGES, please switch to the new (dictionary based) style")
        if getattr(settings, 'LANGUAGE_CODE', '').find('_') > -1:
            section.warn("LANGUAGE_CODE must contain a valid language code, not a locale (e.g.: 'en-us' instead of "
                         "'en_US'): '%s' provided" % getattr(settings, 'LANGUAGE_CODE', ''))
        for lang in getattr(settings, 'LANGUAGES', ()):
            if lang[0].find('_') > -1:
                section.warn("LANGUAGES must contain valid language codes, not locales (e.g.: 'en-us' instead of "
                             "'en_US'): '%s' provided" % lang[0])
        if settings.SITE_ID == hash(settings.SITE_ID):
            for site, items in get_cms_setting('LANGUAGES').items():
                if type(site) == int:
                    for lang in items:
                        if lang['code'].find('_') > -1:
                            section.warn("CMS_LANGUAGES entries must contain valid language codes, not locales (e.g.: "
                                         "'en-us' instead of 'en_US'): '%s' provided" % lang['code'])
        else:
            section.error("SITE_ID must be an integer, not %r" % settings.SITE_ID)


@define_check
def check_middlewares(output):
    with output.section("Middlewares") as section:
        required_middlewares = (
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.CommonMiddleware',
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
            'cms.middleware.language.LanguageCookieMiddleware',
        )
        middlewares = settings.MIDDLEWARE
        for middleware in required_middlewares:
            if middleware not in middlewares:
                section.error("%s middleware must be in MIDDLEWARE" % middleware)

@define_check
def check_context_processors(output):
    with output.section("Context processors") as section:
        processors = list(
            chain(*[template['OPTIONS'].get('context_processors', []) for template in settings.TEMPLATES]))
        required_processors = (
            'cms.context_processors.cms_settings',
        )
        for processor in required_processors:
            if processor not in processors:
                section.error("%s context processor must be in TEMPLATES option context_processors" % processor)


@define_check
def check_plugin_instances(output):
    from cms.management.commands.subcommands.list import plugin_report
    with output.section("Plugin instances") as section:
        # get the report
        report = plugin_report()
        section.success("Plugin instances of %s types found in the database" % len(report))
        # loop over plugin types in the report
        for plugin_type in report:
            # warn about those that are not installed
            if not plugin_type["model"]:
                section.error("%s has instances but is no longer installed" % plugin_type["type"] )
            # warn about those that have unsaved instances
            if plugin_type["unsaved_instances"]:
                section.error(
                    "%s has %s unsaved instances" % (plugin_type["type"], len(plugin_type["unsaved_instances"])))

        if section.successful:
            section.finish_success("The plugins in your database are in good order")
        else:
            section.finish_error("There are potentially serious problems with the plugins in your database. \nEven if "
                                 "your site works, you should run the 'manage.py cms list plugins' \ncommand and then "
                                 "the 'manage.py cms delete-orphaned-plugins' command. \nThis will alter your "
                                 "database; read the documentation before using it.")


@define_check
def check_copy_relations(output):
    from cms.plugin_pool import plugin_pool
    from cms.extensions import extension_pool
    from cms.extensions.models import BaseExtension
    from cms.models.pluginmodel import CMSPlugin

    c_to_s = lambda klass: '%s.%s' % (klass.__module__, klass.__name__)

    def get_class(method_name, model):
        for cls in inspect.getmro(model):
            if method_name in cls.__dict__:
                return cls
        return None

    with output.section('Presence of "copy_relations"') as section:
        plugin_pool.discover_plugins()
        for plugin in plugin_pool.plugins.values():
            plugin_class = plugin.model
            if get_class('copy_relations', plugin_class) is not CMSPlugin or plugin_class is CMSPlugin:
                # this class defines a ``copy_relations`` method, nothing more
                # to do
                continue
            for rel in plugin_class._meta.many_to_many:
                section.warn('%s has a many-to-many relation to %s,\n    but no "copy_relations" method defined.' % (
                    c_to_s(plugin_class),
                    c_to_s(rel.model),
                ))
            for rel in plugin_class._get_related_objects():
                if rel.model != CMSPlugin and not issubclass(rel.model, plugin.model) and rel.model != AliasPluginModel:
                    section.warn('%s has a foreign key from %s,\n    but no "copy_relations" method defined.' % (
                        c_to_s(plugin_class),
                        c_to_s(rel.model),
                    ))

        for extension in chain(extension_pool.page_extensions, extension_pool.title_extensions):
            if get_class('copy_relations', extension) is not BaseExtension:
                # OK, looks like there is a 'copy_relations' defined in the
                # extension... move along...
                continue
            for rel in extension._meta.many_to_many:
                section.warn('%s has a many-to-many relation to %s,\n    '
                             'but no "copy_relations" method defined.' % (
                    c_to_s(extension),
                    c_to_s(rel.remote_field.model),
                ))
            for rel in extension._get_related_objects():
                if rel.model != extension:
                    section.warn('%s has a foreign key from %s,\n    but no "copy_relations" method defined.' % (
                        c_to_s(extension),
                        c_to_s(rel.model),
                    ))

        if not section.warnings:
            section.finish_success('All plugins and page/title extensions have "copy_relations" method if needed.')
        else:
            section.finish_success('Some plugins or page/title extensions do not define a "copy_relations" method.\n'
                                   'This might lead to data loss when publishing or copying plugins/extensions.\n'
                                   'See https://django-cms.readthedocs.io/en/latest/extending_cms/custom_plugins.html#handling-relations or '  # noqa
                                   'https://django-cms.readthedocs.io/en/latest/extending_cms/extending_page_title.html#handling-relations.')  # noqa


def check(output):
    """
    Checks the configuration/environment of this django CMS installation.

    'output' should be an object that provides the same API as FileOutputWrapper.

    Returns whether the configuration/environment are okay (has no errors)
    """
    title = "Checking django CMS installation"
    border = '*' * len(title)
    output.write_line(output.colorize(border, opts=['bold']))
    output.write_line(output.colorize(title, opts=['bold']))
    output.write_line(output.colorize(border, opts=['bold']))
    output.write_line()
    for checker in CHECKERS:
        checker(output)
    output.write_line()
    with output.section("OVERALL RESULTS"):
        if output.errors:
            output.write_stderr_line(output.colorize("%s errors!" % output.errors, opts=['bold'], fg='red'))
        if output.warnings:
            output.write_stderr_line(output.colorize("%s warnings!" % output.warnings, opts=['bold'], fg='yellow'))
        if output.skips:
            output.write_line(output.colorize("%s checks skipped!" % output.skips, opts=['bold'], fg='blue'))
        output.write_line(output.colorize("%s checks successful!" % output.successes, opts=['bold'], fg='green'))
        output.write_line()
        if output.errors:
            output.write_stderr_line(output.colorize('Please check the errors above', opts=['bold'], fg='red'))
        elif output.warnings:
            output.write_stderr_line(output.colorize('Installation okay, but please check warnings above',
                                                     opts=['bold'], fg='yellow'))
        else:
            output.write_line(output.colorize('Installation okay', opts=['bold'], fg='green'))
    return output.successful
