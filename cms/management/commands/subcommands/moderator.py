# -*- coding: utf-8 -*-
from cms.management.commands.subcommands.base import SubcommandsCommand
from cms.models.pagemodel import Page
from django.conf import settings
from django.core.management.base import NoArgsCommand


class ModeratorOnCommand(NoArgsCommand):
    help = 'Turn moderation on, run AFTER setting CMS_MODERATOR = True'
    
    def handle_noargs(self, **options):
        assert settings.CMS_MODERATOR == True, 'Command can only be run if CMS_MODERATOR is True'
        for page in Page.objects.filter(published=True):
            page.publish()


class ModeratorCommand(SubcommandsCommand):
    help = 'Moderator utilities'
    subcommands = {
        'on': ModeratorOnCommand,
    }
