# -*- coding: utf-8 -*-

from django.contrib.sites.models import Site
from django.forms.widgets import Select, MultiWidget, TextInput
from cms.utils.compat.dj import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from cms.forms.utils import get_site_choices, get_page_choices
from cms.models import Page, PageUser
from cms.templatetags.cms_admin import CMS_ADMIN_ICON_BASE


class PageSelectWidget(MultiWidget):
    """A widget that allows selecting a page by first selecting a site and then
    a page on that site in a two step process.
    """
    def __init__(self, site_choices=None, page_choices=None, attrs=None):
        if attrs is not None:
            self.attrs = attrs.copy()
        else:
            self.attrs = {}
        self.choices = []
        super(PageSelectWidget, self).__init__((Select, Select, Select), attrs)

    def decompress(self, value):
        """
        receives a page_id in value and returns the site_id and page_id
        of that page or the current site_id and None if no page_id is given.
        """
        if value:
            page = Page.objects.get(pk=value)
            site = page.site
            return [site.pk, page.pk, page.pk]
        site = Site.objects.get_current()
        return [site.pk,None,None]
    
    def _has_changed(self, initial, data):
        # THIS IS A COPY OF django.forms.widgets.Widget._has_changed()
        # (except for the first if statement)
        
        """
        Return True if data differs from initial.
        """
        # For purposes of seeing whether something has changed, None is
        # the same as an empty string, if the data or inital value we get
        # is None, replace it w/ u''.
        if data is None or (len(data)>=2 and data[1] in [None,'']):
            data_value = u''
        else:
            data_value = data
        if initial is None:
            initial_value = u''
        else:
            initial_value = initial
        if force_unicode(initial_value) != force_unicode(data_value):
            return True
        return False
    
    def render(self, name, value, attrs=None):
        # THIS IS A COPY OF django.forms.widgets.MultiWidget.render()
        # (except for the last line)
        
        # value is a list of values, each corresponding to a widget
        # in self.widgets.

        site_choices = get_site_choices()
        page_choices = get_page_choices()
        self.site_choices = site_choices
        self.choices = page_choices
        self.widgets = (Select(choices=site_choices ),
                   Select(choices=[('', '----')]),
                   Select(choices=self.choices, attrs={'style': "display:none;"} ),
        )

        if not isinstance(value, list):
            value = self.decompress(value)
        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id', None)
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))
            output.append(widget.render(name + '_%s' % i, widget_value, final_attrs))
        output.append(r'''<script type="text/javascript">
(function($) {
    var handleSiteChange = function(site_name, selected_id) {
        $("#id_%(name)s_1 optgroup").remove();
        var myOptions = $("#id_%(name)s_2 optgroup[label='" + site_name + "']").clone();
        $("#id_%(name)s_1").append(myOptions);
        $("#id_%(name)s_1").change();
    };
    var handlePageChange = function(page_id) {
        if (page_id) {
            $("#id_%(name)s_2 option").removeAttr('selected');
            $("#id_%(name)s_2 option[value=" + page_id + "]").attr('selected','selected');
        } else {
            $("#id_%(name)s_2 option[value=]").attr('selected','selected');
        };
    };
    $("#id_%(name)s_0").change(function(){
        var site_label = $("#id_%(name)s_0").children(":selected").text();
        handleSiteChange( site_label );
    });
    $("#id_%(name)s_1").change(function(){
        var page_id = $(this).find('option:selected').val();
        handlePageChange( page_id );
    });
    $(function(){
        handleSiteChange( $("#id_%(name)s_0").children(":selected").text() );
        $("#add_id_%(name)s").hide();
    });
})(django.jQuery);
</script>''' % {'name': name})
        return mark_safe(self.format_output(output))
    
    def format_output(self, rendered_widgets):
        return u' '.join(rendered_widgets)

class PageSmartLinkWidget(TextInput):



    def render(self, name=None, value=None, attrs=None):
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id', None)

        output = [r'''<script type="text/javascript">
(function($){
    $(function(){
        $("#%(element_id)s").select2({
            placeholder: "%(placeholder_text)s",
            minimumInputLength: 3,
            ajax: {
                url: "/%(language_code)s/admin/cms/page/published/",
                dataType: 'json',
                data: function (term, page) {
                    return {
                        q: term, // search term
                        language_code: '%(language_code)s'
                    };
                },
                results: function (data, page) {
                    return {
                        more: false,
                        results: $.map(data, function(item, i){
                            return {
                                'id':item.title_set__path,
                                'text': item.title_set__title + ' (/' + item.title_set__path + ')'}
                            }
                        )
                    };
                }
            },
            // Allow creation of new entries
            createSearchChoice:function(term, data) { if ($(data).filter(function() { return this.text.localeCompare(term)===0; }).length===0) {return {id:term, text:term};} },
            multiple: false,
            initSelection : function (element, callback) {
                var initialValue = element.val()
                callback({id:initialValue, text: initialValue});
            }
        });
    })
})(django.jQuery);
</script>''' % {
            'element_id': id_,
            'placeholder_text': final_attrs.get('placeholder_text', ''),
            'language_code': self.language
        }]

        output.append(super(PageSmartLinkWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))


    class Media:
        css = {
            'all': ('cms/js/select2/select2.css',
                    'cms/js/select2/select2-bootstrap.css',)
        }
        js = (#'cms/js/libs/jquery.min.js',
              'cms/js/select2/select2.js',)


class UserSelectAdminWidget(Select):
    """Special widget used in page permission inlines, because we have to render
    an add user (plus) icon, but point it somewhere else - to special user creation
    view, which is accessible only if user haves "add user" permissions.
    
    Current user should be assigned to widget in form constructor as an user 
    attribute.
    """
    def render(self, name, value, attrs=None, choices=()):
        output = [super(UserSelectAdminWidget, self).render(name, value, attrs, choices)]    
        if hasattr(self, 'user') and (self.user.is_superuser or \
            self.user.has_perm(PageUser._meta.app_label + '.' + PageUser._meta.get_add_permission())):
            # append + icon
            add_url = '../../../cms/pageuser/add/'
            output.append(u'<a href="%s" class="add-another" id="add_id_%s" onclick="return showAddAnotherPopup(this);"> ' % \
                    (add_url, name))
            output.append(u'<img src="%sicon_addlink.gif" width="10" height="10" alt="%s"/></a>' % (CMS_ADMIN_ICON_BASE, _('Add Another')))
        return mark_safe(u''.join(output))
    
