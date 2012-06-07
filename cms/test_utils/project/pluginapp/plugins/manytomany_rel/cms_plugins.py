from django.utils.translation import ugettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from cms.test_utils.project.pluginapp.plugins.manytomany_rel.models import ArticlePluginModel
from cms.test_utils.project.pluginapp.models import Article



class ArticlePlugin(CMSPluginBase):
    model = ArticlePluginModel
    name = _("Articles")
    render_template = "newsroom/plugins/articles.html"
    admin_preview = False

    def render(self, context, instance, placeholder):
        article_qs = Article.published_objects.all(section__name__in=instance.sections)        
        context.update({'instance':instance,
                        'article_qs':article_qs,
                        'placeholder':placeholder})
        return context
    
plugin_pool.register_plugin(ArticlePlugin)
