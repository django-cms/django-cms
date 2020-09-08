from django.core.management.base import CommandError

from cms.utils.check import FileOutputWrapper, check

from .base import SubcommandsCommand


class CheckInstallation(SubcommandsCommand):
    help_string = 'Checks your settings and environment'
    command_name = 'check'

    def handle(self, *args, **options):
        if not check(FileOutputWrapper(self.stdout, self.stderr)):
            raise CommandError()
