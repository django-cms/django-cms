from django.utils.translation import ugettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from cms.test_utils.project.pluginapp.plugins.manytomany_rel.models import (
    ArticlePluginModel, Article,
    PluginModelWithFKFromModel,
    PluginModelWithM2MToModel,
    FKPluginModel,
    M2MTargetPluginModel,
    PluginModelWithFKFromPlugin,
    PluginModelWithM2MToPlugin,
)


class ArticlePlugin(CMSPluginBase):
    model = ArticlePluginModel
    name = _("Articles")
    render_template = "articles.html"
    admin_preview = False

    def render(self, context, instance, placeholder):
        article_qs = Article.objects.filter(section__in=instance.sections.all())
        context.update({'instance': instance,
                        'article_qs': article_qs,
                        'placeholder': placeholder})
        return context

plugin_pool.register_plugin(ArticlePlugin)


class ArticleDynamicTemplatePlugin(CMSPluginBase):
    model = ArticlePluginModel
    name = _("Articles")
    admin_preview = False

    def get_render_template(self, context, instance, placeholder):
        if instance.title == 'custom template':
            return "articles_custom.html"
        else:
            return "articles.html"

    def render(self, context, instance, placeholder):
        article_qs = Article.objects.filter(section__in=instance.sections.all())
        context.update({'instance': instance,
                        'article_qs': article_qs,
                        'placeholder': placeholder})
        return context

plugin_pool.register_plugin(ArticleDynamicTemplatePlugin)


###


class PluginWithFKFromModel(CMSPluginBase):
    model = PluginModelWithFKFromModel
    render_template = "articles.html"

plugin_pool.register_plugin(PluginWithFKFromModel)


class PluginWithM2MToModel(CMSPluginBase):
    model = PluginModelWithM2MToModel
    render_template = "articles.html"

plugin_pool.register_plugin(PluginWithM2MToModel)


class FKPlugin(CMSPluginBase):
    model = FKPluginModel
    render_template = "articles.html"

plugin_pool.register_plugin(FKPlugin)


class M2MTargetPlugin(CMSPluginBase):
    model = M2MTargetPluginModel
    render_template = "articles.html"

plugin_pool.register_plugin(M2MTargetPlugin)


class PluginWithFKFromPlugin(CMSPluginBase):
    model = PluginModelWithFKFromPlugin
    render_template = "articles.html"

plugin_pool.register_plugin(PluginWithFKFromPlugin)


class PluginWithM2MToPlugin(CMSPluginBase):
    model = PluginModelWithM2MToPlugin
    render_template = "articles.html"

plugin_pool.register_plugin(PluginWithM2MToPlugin)
