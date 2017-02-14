..  _complex_plugins:


##########################
Complex plugin integration
##########################

****************************************
Overview of how django CMS wraps plugins
****************************************

A django CMS plugin editing interface is fundamentally a Django admin interface for the model object in question,
wrapped with some additional layers to present it in a way that's appropriate to the editing task and workflow.

The wrapping looks a bit like this:

* ``<div class="cms-modal-iframe>...</div>``, a modal dialog box, containing

  * ``<iframe...>``, which contains

    * ``<html>...</html>``, the actual Django admin page

In order to present a consistent interface to the user, django CMS overrides some parts of the interface Django
provides.

For example, the Django admin provides a ``<div class="submit-row">`` for forms, that contains **Save** and **Delete**
buttons. In a standard Django admin page, **Save** is actually an ``<input type="submit">`` and **Delete** is simply a
link.

django CMS hides the ``div.submit-row`` (with ``visibility: none``) and instead provides its own buttons: **Cancel**,
**Delete** and **Save**.

The plugin wrapper moves the functionality of Django buttons is moved from within the ``<html>...</html>`` to the
``<div class="cms-modal-iframe>...</div>``.

As far as the user is concerned, the wrapper must (and must) behave transparently. For example, **Save** must do what
it would in a standard admin form page, including validation and cleaning, and the same for any inlined admin objects.

This allows django CMS to perform some additional actions, such as tidying up the structure mode display when the
modal  dialog box is closed.

How wrapping is implemented
***************************

In order to achieve this, django CMS refers the **Save** and **Delete** actions to the admin form.

Hitting django CMS's **Save** button invokes the ``<input>`` on the admin form, as though it had been invoked in the
browser by the user, by assigning its own **Save** button to the form's ``submit`` event.

.. todo: Anything else we should note?


********************
More complex plugins
********************

For most Django admin pages that the plugin system wraps, this is fairly straighforward.

Some plugins however are more complex, and have their own custom forms and widgets.

An example of this is the default `text django CMS CKEditor plugin <https://github.com/divio/djangocms-text-ckeditor>`_.

This plugin uses a Django form :class:`Textarea widget <django:django.forms.Textarea>`, which creates an HTML
``<textarea>`` - *which it hides*. It then creates its own text-editing interface, the familiar CKEditor, and on
**Save** parses the content in that (some of which may not be text content, such as plugins) and places it in the
textarea.

The textarea is then saved in the normal way; if there are any plugins contained in it they will be saved to the
database before the operation can finally be considered to have concluded successfully.

.. todo: the saving of the plugins in the text editor is done in Python, not JS, correct?

.. todo:

    If the modal's Save invokes form's submit in such a way that it can successfully run the JS validation on form
    elements, why does it not also invoke the JS that an editor plugin uses to transfer the editor content back to the
    textarea? It's now not clear to me why it's necessary for the CKEditor to do this separately in
    https://github.com/divio/djangocms-text-ckeditor/blob/24de3e94cc31e934f17f6b061b05bf13aee042cd/djangocms_text_ckedit
    or/static/djangocms_text_ckeditor/ckeditor_plugins/cmsplugins/plugin.js#L171-L221.
