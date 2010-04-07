from django.contrib import admin
from cms.admin.placeholderadmin import PlaceholderAdmin
from sampleblog.models import BlogPost

admin.site.register(BlogPost, PlaceholderAdmin)
