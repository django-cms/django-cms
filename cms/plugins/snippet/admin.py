from models import Snippet
from django.contrib import admin

class SnippetAdmin(admin.ModelAdmin):
    pass

admin.site.register(Snippet, SnippetAdmin)
