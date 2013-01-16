# -*- coding: utf-8 -*-
from collections import namedtuple
from contextlib import contextmanager
from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.termcolors import colorize

SUCCESS = 1
WARNING = 2
ERROR = 3
SKIPPED = 4

CHECKERS = []

CheckSection = namedtuple('CheckSection', 'title result subchecks')
CheckResult = namedtuple('CheckResult', 'name result info')


class FileOutputWrapper(object):
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
        self.stderr.write(u'%s\n' % message)

    def write_stderr(self, message):
        self.stderr.write(message)

    def success(self, message):
        self.successes += 1
        self.write_line(u'%s %s' % (message, self.colorize('[OK]', fg='green', opts=['bold'])))

    def error(self, message):
        self.errors += 1
        self.write_stderr_line(u'%s %s' % (message, self.colorize('[ERROR]', fg='red', opts=['bold'])))

    def warning(self, message):
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
    def __init__(self, wrapper):
        super(FileSectionWrapper, self).__init__(wrapper.stdout, wrapper.stderr)
        self.wrapper = wrapper

    def write_line(self, message=''):
        self.write(u'  - %s\n' % message)

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
    CHECKERS.append(func)
    return func


@define_check
def check_sekizai(output):
    with output.section("Sekizai") as section:
        if 'sekizai' in settings.INSTALLED_APPS:
            section.success("Sekizai is installed")
        else:
            section.error("Sekizai is not installed, could not find 'sekizai' in INSTALLED_APPS")
        if 'sekizai.context_processors.sekizai' in settings.TEMPLATE_CONTEXT_PROCESSORS:
            section.success("Sekizai template context processor is installed")
        else:
            section.error("Sekizai template context processor is not install, could not find 'sekizai.context_processors.sekizai' in TEMPLATE_CONTEXT_PROCESSORS")
        section.finish_success("Sekizai configuration okay")

def check(output):
    title = "Checking django CMS installation"
    border = '*' * len(title)
    output.write_line(output.colorize(border, opts=['bold']))
    output.write_line(output.colorize(title, opts=['bold']))
    output.write_line(output.colorize(border, opts=['bold']))
    output.write_line()
    for checker in CHECKERS:
        checker(output)
    output.write_line()
    with output.section("OVERALL RESULTS") as section:
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
            output.write_stderr_line(output.colorize('Installation okay, but please check warnings above', opts=['bold'], fg='yellow'))
        else:
            output.write_line(output.colorize('Installation okay', opts=['bold'], fg='green'))
    return output.successful
