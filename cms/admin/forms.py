from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.forms.util import ErrorList
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import BooleanField

from cms import settings as cms_settings
from cms.models import Page, Title, PagePermission, ExtUser, ACCESS_PAGE
from cms.utils.urlutils import any_path_re
from cms.utils.permissions import get_current_user, get_subordinate_users,\
    get_subordinate_groups
from cms.admin.widgets import UserSelectAdminWidget

    
class PageForm(forms.ModelForm):
    APPLICATION_URLS = (('', '----------'), ) + cms_settings.CMS_APPLICATIONS_URLS
    
    title = forms.CharField(label=_("Title"), widget=forms.TextInput(),
        help_text=_('The default title'))
    language = forms.ChoiceField(label=_("Language"), choices=cms_settings.CMS_LANGUAGES,
        help_text=_('The current language of the content fields.'))
    slug = forms.CharField(label=_("Slug"), widget=forms.TextInput(),
        help_text=_('The part of the title that is used in the url'))
    application_urls = forms.ChoiceField(label=_('Application'), 
        choices=APPLICATION_URLS, required=False,  
        help_text=_('Hook application to this page.'))
    overwrite_url = forms.CharField(label='Overwrite url', max_length=255, required=False,
        help_text=_('Keep this field empty if standard path should be used.'))
    # moderation state
    moderator_state = forms.IntegerField(widget=forms.HiddenInput, required=False, initial=Page.MODERATOR_CHANGED) 
    # moderation - message is a fake filed
    moderator_message = forms.CharField(max_length=1000, widget=forms.HiddenInput, required=False)
    
    
    class Meta:
        model = Page
    
    def clean(self):
        cleaned_data = self.cleaned_data
        if 'slug' in cleaned_data.keys():
            slug = cleaned_data['slug']
        else:
            slug = ""
        
        page = self.instance
        lang = cleaned_data['language']
        parent = cleaned_data['parent']
        if cms_settings.CMS_UNIQUE_SLUGS:
            titles = Title.objects.filter(slug=slug)
        else:
            titles = Title.objects.filter(slug=slug, language=lang)        
        if not cms_settings.CMS_FLAT_URLS:
            titles = titles.filter(page__parent=parent)
        if self.instance.pk:
            titles = titles.exclude(language=lang, page=page)
        if titles.count():
            self._errors['slug'] = ErrorList([ugettext_lazy('Another page with this slug already exists')])
            del cleaned_data['slug']
        return cleaned_data
    
    def clean_slug(self):
        slug = slugify(self.cleaned_data['slug'])
        return slug
    
    def clean_reverse_id(self):
        id = self.cleaned_data['reverse_id']
        if id:
            if Page.objects.filter(reverse_id=id).exclude(pk=self.instance.pk).count():
                raise forms.ValidationError(ugettext_lazy('A page with this reverse url id exists already.'))
        return id

    def clean_overwrite_url(self):
        url = self.cleaned_data['overwrite_url']
        if url:
            if not any_path_re.match(url):
                raise forms.ValidationError(ugettext_lazy('Invalid url, use /my/url format.'))
        return url
    
    def clean_sites(self):
        sites = self.cleaned_data['sites']
        if self.cleaned_data['parent'] != None:
            parent_sites = self.cleaned_data['parent'].sites.all().values_list('id', flat=True)
            for site in sites:
                if not site.pk in parent_sites:
                    raise forms.ValidationError(ugettext_lazy('The parent of this page is not on the site %(site)s') % {'site':site } )
        return sites


class PagePermissionInlineAdminForm(forms.ModelForm):
    """Page permission inline admin form used in inline admin. Required, because
    user and group queryset must be changed. User can see only users on the same
    level or under him in choosen page tree, and users which were created by him, 
    but aren't assigned to higher page level than current user.
    """
    
    user = forms.ModelChoiceField(_('user'), widget=UserSelectAdminWidget)
    
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None):
        
        super(PagePermissionInlineAdminForm, self).__init__(data, files,
            auto_id, prefix, initial, error_class, label_suffix, empty_permitted,
            instance)
        
        user = get_current_user() # current user from threadlocals
        
        self.fields['user'].queryset=get_subordinate_users(user)
        self.fields['user'].widget.user = user # assign current user
        self.fields['group'].queryset=get_subordinate_groups(user)
        
    def clean(self):
        super(PagePermissionInlineAdminForm, self).clean()
        for field in self.Meta.model._meta.fields:
            if not isinstance(field, BooleanField) or not field.name.startswith('can_'):
                continue
            name = field.name
            self.cleaned_data[name] = self.cleaned_data.get(name, False)
        
        can_add = self.cleaned_data['can_add']
        # check if access for childrens, or descendants is granted
        if can_add and self.cleaned_data['grant_on'] == ACCESS_PAGE:
            # this is a missconfiguration - user can add/move page to current
            # page but after he does this, he will not have permissions to 
            # access this page anymore, so avoid this
            raise forms.ValidationError(ugettext_lazy('Add page permission requires also access to children, or descendants, otherwise added page can\'t be changed by his creator.'))
        
        # TODO: finish this, but is it really required? might be nice to have 
        
        # check if permissions assigned in cms are correct, and display an message
        # if not - correctness mean: if user has add permisson to page, but he
        # does'nt have auth permissions to add page object, display warning
        return self.cleaned_data
    
    def save(self, commit=True):
        """Boolean fields lacks, if they aren't available in the form, they are
        taking default value, but we actually wan't false for them.
        """        
        instance = super(PagePermissionInlineAdminForm, self).save(commit=False)
        for field in self.Meta.model._meta.fields:
            if not isinstance(field, BooleanField) or not field.name.startswith('can_'):
                continue
            name = field.name
            setattr(instance, name, self.cleaned_data.get(name, False))
        if commit:
            instance.save()
        return instance
    

class ExtUserCreationForm(UserCreationForm):
    can_add_page = forms.BooleanField(label=_('Can add page'), required=False, initial=True)
    can_change_page = forms.BooleanField(label=_('Can change page'), required=False, initial=True)
    can_delete_page = forms.BooleanField(label=_('Can delete page'), required=False)
    
    can_add_user = forms.BooleanField(label=_('Can create user'), required=False)
    can_change_user = forms.BooleanField(label=_('Can change User'), required=False)
    can_delete_user = forms.BooleanField(label=_('Can delete User'), required=False)
    
    can_add_pagepermission = forms.BooleanField(label=_('Can add page permission'), required=False)
    can_change_pagepermission = forms.BooleanField(label=_('Can change page permission'), required=False)
    can_delete_pagepermission = forms.BooleanField(label=_('Can delete page permission'), required=False)
    
    class Meta:
        model = ExtUser
    
    def save(self, commit=True):
        """Create user, assign him to staff users, and create permissions for 
        him if required. Also assigns creator to user.
        """
        user = super(ExtUserCreationForm, self).save(commit=False)
        user.is_staff=True
        # assign creator to user
        user.created_by = get_current_user()
        
        models = (Page, User, PagePermission)
        
        if commit:
            user.save()
        
        for model in models:
            name = model.__name__.lower()
            content_type = ContentType.objects.get_for_model(model)
            for t in ('add', 'change', 'delete'):
                if not self.cleaned_data.get('can_%s_%s' % (t, name), None):
                    continue
                if not user.pk:
                    # save user, otherwise we can't assign permissions to him
                    user.save()
                
                # add permission `t` to model `model`
                codename = getattr(model._meta, 'get_%s_permission' % t)()
                permission = Permission.objects.get(content_type=content_type, codename=codename)
                user.user_permissions.add(permission)
        return user