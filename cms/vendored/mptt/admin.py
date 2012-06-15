
import django
from django.conf import settings
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.options import ModelAdmin, IncorrectLookupParameters
from django import template
from django.contrib.admin import helpers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.utils.encoding import force_unicode

from .forms import MPTTAdminForm, TreeNodeChoiceField

__all__ = ('MPTTChangeList', 'MPTTModelAdmin', 'MPTTAdminForm')


class MPTTChangeList(ChangeList):
    def get_query_set(self, request=None):
        # request arg was added in django r16144 (after 1.3)
        if request is not None and django.VERSION >= (1, 4):
            qs = super(MPTTChangeList, self).get_query_set(request)
        else:
            qs = super(MPTTChangeList, self).get_query_set()

        # always order by (tree_id, left)
        tree_id = qs.model._mptt_meta.tree_id_attr
        left = qs.model._mptt_meta.left_attr
        return qs.order_by(tree_id, left)


class MPTTModelAdmin(ModelAdmin):
    """
    A basic admin class that displays tree items according to their position in the tree.
    No extra editing functionality beyond what Django admin normally offers.
    """

    change_list_template = 'admin/mptt_change_list.html'

    form = MPTTAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        from .models import MPTTModel, TreeForeignKey
        if issubclass(db_field.rel.to, MPTTModel) and not isinstance(db_field, TreeForeignKey):
            defaults = dict(form_class=TreeNodeChoiceField, queryset=db_field.rel.to.objects.all(), required=False)
            defaults.update(kwargs)
            kwargs = defaults
        return super(MPTTModelAdmin, self).formfield_for_foreignkey(db_field,
                                                                    request,
                                                                    **kwargs)

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        return MPTTChangeList

    # In Django 1.1, the changelist class is hard coded in changelist_view, so
    # we've got to override this too, just to get it to use our custom ChangeList
    if django.VERSION < (1, 2):
        def changelist_view(self, request, extra_context=None):
            "The 'change list' admin view for this model."
            from django.contrib.admin.views.main import ERROR_FLAG
            opts = self.model._meta
            app_label = opts.app_label
            if not self.has_change_permission(request, None):
                raise PermissionDenied

            # Check actions to see if any are available on this changelist
            actions = self.get_actions(request)

            # Remove action checkboxes if there aren't any actions available.
            list_display = list(self.list_display)
            if not actions:
                try:
                    list_display.remove('action_checkbox')
                except ValueError:
                    pass

            CL = self.get_changelist(request)

            try:
                cl = CL(request, self.model, list_display, self.list_display_links, self.list_filter,
                    self.date_hierarchy, self.search_fields, self.list_select_related, self.list_per_page, self.list_editable, self)
            except IncorrectLookupParameters:
                # Wacky lookup parameters were given, so redirect to the main
                # changelist page, without parameters, and pass an 'invalid=1'
                # parameter via the query string. If wacky parameters were given and
                # the 'invalid=1' parameter was already in the query string, something
                # is screwed up with the database, so display an error page.
                if ERROR_FLAG in request.GET.keys():
                    return render_to_response('admin/invalid_setup.html', {'title': _('Database error')})
                return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

            # If the request was POSTed, this might be a bulk action or a bulk edit.
            # Try to look up an action or confirmation first, but if this isn't an
            # action the POST will fall through to the bulk edit check, below.
            if actions and request.method == 'POST' and (helpers.ACTION_CHECKBOX_NAME in request.POST or 'index' in request.POST):
                response = self.response_action(request, queryset=cl.get_query_set(request))
                if response:
                    return response

            # If we're allowing changelist editing, we need to construct a formset
            # for the changelist given all the fields to be edited. Then we'll
            # use the formset to validate/process POSTed data.
            formset = cl.formset = None

            # Handle POSTed bulk-edit data.
            if request.method == "POST" and self.list_editable:
                FormSet = self.get_changelist_formset(request)
                formset = cl.formset = FormSet(request.POST, request.FILES, queryset=cl.result_list)
                if formset.is_valid():
                    changecount = 0
                    for form in formset.forms:
                        if form.has_changed():
                            obj = self.save_form(request, form, change=True)
                            self.save_model(request, obj, form, change=True)
                            form.save_m2m()
                            change_msg = self.construct_change_message(request, form, None)
                            self.log_change(request, obj, change_msg)
                            changecount += 1

                    if changecount:
                        if changecount == 1:
                            name = force_unicode(opts.verbose_name)
                        else:
                            name = force_unicode(opts.verbose_name_plural)
                        msg = ungettext("%(count)s %(name)s was changed successfully.",
                                        "%(count)s %(name)s were changed successfully.",
                                        changecount) % {'count': changecount,
                                                        'name': name,
                                                        'obj': force_unicode(obj)}
                        self.message_user(request, msg)

                    return HttpResponseRedirect(request.get_full_path())

            # Handle GET -- construct a formset for display.
            elif self.list_editable:
                FormSet = self.get_changelist_formset(request)
                formset = cl.formset = FormSet(queryset=cl.result_list)

            # Build the list of media to be used by the formset.
            if formset:
                media = self.media + formset.media
            else:
                media = self.media

            # Build the action form and populate it with available actions.
            if actions:
                action_form = self.action_form(auto_id=None)
                action_form.fields['action'].choices = self.get_action_choices(request)
            else:
                action_form = None

            context = {
                'title': cl.title,
                'is_popup': cl.is_popup,
                'cl': cl,
                'media': media,
                'has_add_permission': self.has_add_permission(request),
                'root_path': self.admin_site.root_path,
                'app_label': app_label,
                'action_form': action_form,
                'actions_on_top': self.actions_on_top,
                'actions_on_bottom': self.actions_on_bottom,
            }
            context.update(extra_context or {})
            context_instance = template.RequestContext(request, current_app=self.admin_site.name)
            return render_to_response(self.change_list_template or [
                'admin/%s/%s/change_list.html' % (app_label, opts.object_name.lower()),
                'admin/%s/change_list.html' % app_label,
                'admin/change_list.html'
            ], context, context_instance=context_instance)
