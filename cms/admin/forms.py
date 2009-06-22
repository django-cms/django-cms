from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.forms.util import ErrorList
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import BooleanField

from cms import settings as cms_settings
from cms.models import Page, Title, PagePermission, PageUser, ACCESS_PAGE
from cms.utils.urlutils import any_path_re
from cms.utils.permissions import get_current_user, get_subordinate_users,\
    get_subordinate_groups, mail_page_user_change
from cms.admin.widgets import UserSelectAdminWidget
from cms.utils.page import is_valid_page_slug
from django.forms.widgets import HiddenInput

    
class PageForm(forms.ModelForm):
    APPLICATION_URLS = (('', '----------'), ) + cms_settings.CMS_APPLICATIONS_URLS
    
    title = forms.CharField(label=_("Title"), widget=forms.TextInput(),
        help_text=_('The default title'))
    menu_title = forms.CharField(label=_("Menu Title"), widget=forms.TextInput(),
        help_text=_('Overwrite what is displayed in the menu'), required=False)
    page_title = forms.CharField(label=_("Page Title"), widget=forms.TextInput(),
        help_text=_('Overwrites what is display at the top of your browser or in bookmarks'), required=False)
    language = forms.ChoiceField(label=_("Language"), choices=cms_settings.CMS_LANGUAGES,
        help_text=_('The current language of the content fields.'))
    slug = forms.CharField(label=_("Slug"), widget=forms.TextInput(),
        help_text=_('The part of the title that is used in the url'))
    application_urls = forms.ChoiceField(label=_('Application'), 
        choices=APPLICATION_URLS, required=False,  
        help_text=_('Hook application to this page.'))
    overwrite_url = forms.CharField(label=_('Overwrite url'), max_length=255, required=False,
        help_text=_('Keep this field empty if standard path should be used.'))
    # moderation state
    moderator_state = forms.IntegerField(widget=forms.HiddenInput, required=False, initial=Page.MODERATOR_CHANGED) 
    # moderation - message is a fake filed
    moderator_message = forms.CharField(max_length=1000, widget=forms.HiddenInput, required=False)
    
    redirect = forms.CharField(label=_('Redirect'), max_length=255, required=False,
        help_text=_('Redirects to this URL.'))
    meta_description = forms.CharField(label='Description meta tag', required=False, widget=forms.Textarea,
        help_text=_('A description of the page sometimes used by search engines.'))
    meta_keywords = forms.CharField(label='Keywords meta tag', max_length=255, required=False,
        help_text=_('A list of comma seperated keywords sometimes used by search engines.'))    
    
    class Meta:
        model = Page
        
    def __init__(self, *args, **kwargs):
        super(PageForm, self).__init__(*args, **kwargs)
        self.fields['parent'].widget = HiddenInput()
        self.fields['parent'].label = "" 
        self.fields['site'].widget = HiddenInput()
        self.fields['site'].label = ""
        self.fields['site'].help_text = "" 
    
    def clean(self):
        cleaned_data = self.cleaned_data
        if 'slug' in cleaned_data.keys():
            slug = cleaned_data['slug']
        else:
            slug = ""
        page = self.instance
        lang = cleaned_data['language']
        if 'parent' not in cleaned_data:
            cleaned_data['parent'] = None
        parent = cleaned_data.get('parent', None)
        if not is_valid_page_slug(page, parent, lang, slug):
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
    

class PagePermissionInlineAdminForm(forms.ModelForm):
    """Page permission inline admin form used in inline admin. Required, because
    user and group queryset must be changed. User can see only users on the same
    level or under him in choosen page tree, and users which were created by him, 
    but aren't assigned to higher page level than current user.
    """
    
    user = forms.ModelChoiceField('user', label=_('user'), widget=UserSelectAdminWidget, required=False)
    page = forms.ModelChoiceField(Page, label=_('user'), widget=HiddenInput(), required=True)
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
        can_edit = self.cleaned_data['can_change']
        # check if access for childrens, or descendants is granted
        if can_add and self.cleaned_data['grant_on'] == ACCESS_PAGE:
            # this is a missconfiguration - user can add/move page to current
            # page but after he does this, he will not have permissions to 
            # access this page anymore, so avoid this
            raise forms.ValidationError(ugettext_lazy('Add page permission requires also access to children, or descendants, otherwise added page can\'t be changed by his creator.'))
        
        if can_add and not can_edit:
            raise forms.ValidationError(ugettext_lazy('Add page permission also requires edit page permission.'))
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
    

class PageUserForm(UserCreationForm):
    can_add_page = forms.BooleanField(label=_('Can add page'), required=False, initial=True)
    can_change_page = forms.BooleanField(label=_('Can change page'), required=False, initial=True)
    can_delete_page = forms.BooleanField(label=_('Can delete page'), required=False)
    can_recover_page = forms.BooleanField(label=_('Can recover pages (any)'), required=False)
    
    can_add_pageuser = forms.BooleanField(label=_('Can create user'), required=False)
    can_change_pageuser = forms.BooleanField(label=_('Can change User'), required=False)
    can_delete_pageuser = forms.BooleanField(label=_('Can delete User'), required=False)
    
    can_add_pagepermission = forms.BooleanField(label=_('Can add page permission'), required=False)
    can_change_pagepermission = forms.BooleanField(label=_('Can change page permission'), required=False)
    can_delete_pagepermission = forms.BooleanField(label=_('Can delete page permission'), required=False)
    
    notify_user = forms.BooleanField(label=_('Notify user'), required=False, 
        help_text=_('Send email notification to user about username or password change. Requires user email.'))
    
    class Meta:
        model = PageUser
    
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None):
        
        if instance:
            initial = initial or {}
            initial.update(self.populate_initials(instance))
        
        super(PageUserForm, self).__init__(data, files, auto_id, prefix, 
            initial, error_class, label_suffix, empty_permitted, instance)
        
        if instance:
            # if it is a change form, keep those fields as not required
            # password will be changed only if there is something entered inside
            self.fields['password1'].required = False
            self.fields['password1'].label = _('New password')
            self.fields['password2'].required = False
            self.fields['password2'].label = _('New password confirmation')
        
        self._password_change = True
        
    def populate_initials(self, instance):
        """Read out user permissions from permission system.
        """
        initials = {}
        models = (Page, PageUser, PagePermission)
        for model in models:
            name = model.__name__.lower()
            for t in ('add', 'change', 'delete'):
                codename = getattr(model._meta, 'get_%s_permission' % t)()
                initials['can_%s_%s' % (t, name)] = instance.has_perm('%s.%s' % (model._meta.app_label, codename)) 
        return initials        
        
    def clean_username(self):
        if self.instance:
            return self.cleaned_data['username']
        return super(PageUserForm, self).clean_username()
    
    def clean_password2(self): 
        if self.instance and self.cleaned_data['password1'] == '' and self.cleaned_data['password2'] == '':
            self._password_change = False
            return u''
        return super(PageUserForm, self).clean_password2()

    def clean(self):
        cleaned_data = super(PageUserForm, self).clean()
        notify_user = self.cleaned_data['notify_user']
        if notify_user and not self.cleaned_data.get('email', None):
            raise forms.ValidationError(_("Email notification requires valid email address."))
        return cleaned_data

    def save(self, commit=True):
        """Create user, assign him to staff users, and create permissions for 
        him if required. Also assigns creator to user.
        """
        Super = self._password_change and PageUserForm or UserCreationForm  
        user = super(Super, self).save(commit=False)
        
        user.is_staff = True
        created = not bool(user.pk)
        # assign creator to user
        if created:
            user.created_by = get_current_user()

        if commit:
            user.save()

        models = (Page, PageUser, PagePermission)
        for model in models:
            name = model.__name__.lower()
            content_type = ContentType.objects.get_for_model(model)
            for t in ('add', 'change', 'delete'):
                if not user.pk:
                    # save user, otherwise we can't assign permissions to him
                    user.save()
                
                # add permission `t` to model `model`
                codename = getattr(model._meta, 'get_%s_permission' % t)()
                permission = Permission.objects.get(content_type=content_type, codename=codename)
                
                if self.cleaned_data.get('can_%s_%s' % (t, name), None):
                    user.user_permissions.add(permission)
                else:
                    user.user_permissions.remove(permission)

        if self.cleaned_data['notify_user']:
            mail_page_user_change(user, created, self.cleaned_data['password1'])
        
        return user