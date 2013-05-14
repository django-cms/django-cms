# -*- coding: utf-8 -*-
from cms.management.commands.subcommands.base import SubcommandsCommand
from cms.models import CMSPlugin
from cms.models.pagemodel import Page
from django.core.management.base import NoArgsCommand
from django.db import transaction


class ModeratorOnCommand(NoArgsCommand):
    help = 'Turn moderation on, run AFTER upgrading to 2.4'
    
    def handle_noargs(self, **options):
        """
        Ensure that the public pages look the same as their draft versions.
        This is done by checking the content of the public pages, and reverting
        the draft version to look the same.

        The second stage is to go through the draft pages and publish the ones
        marked as published.

        The end result should be that the public pages and their draft versions
        have the same plugins listed. If both versions exist and have content,
        the public page has precedence. Otherwise, the draft version is used.
        """
        with transaction.commit_on_success():
            pages_public = list(Page.objects.public())
            for i, page in enumerate(pages_public):
                self.stdout.write("Stage 1: Processing page %s - %d / %d"  % (page, i, len(pages_public)))
                if CMSPlugin.objects.filter(placeholder__page=page).count():
                    page.publisher_draft.revert()

            pages_drafts = list(Page.objects.drafts().filter(published=True))
            for i, page in enumerate(pages_drafts):
                self.stdout.write("Stage 2: Processing page '%s:%s' - %d / %d " % (page.id, page, i, len(pages_drafts)))
                page.publish()


class ModeratorCommand(SubcommandsCommand):
    help = 'Moderator utilities'
    subcommands = {
        'on': ModeratorOnCommand,
    }
