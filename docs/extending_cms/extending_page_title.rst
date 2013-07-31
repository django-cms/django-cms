################################
Extending the page & title model
################################

If you want to extend the page or title model with your own fields e.g. adding an icon for every page the extension models are the way to go.


HowTo
=====

To add a field to the page model create a class that inherits from ``cms.models.pageextensionmodel.PageExtension``. Make sure to import the PageExtension model straight from the given path. It isn't importable from cms.models.
Your class should live in one of your apps ``models.py``. You are free to add every field you want but make sure you doesn't use a unique constraint on any of your added fields because uniqueness prevents the copy mechanism of the extension. This forbids the use of OneToOne relations on the ExtensionModel.


Hooking the extension to the admin site
=======================================

To show your created extension in the admin interface you could use the ``PageExtensionAdmin`` in ``cms.admin.pageextensionadmin``. If you want to use your own admin class make sure to exclude the live versions of the extensions by using ``filter(extended_page__publisher_is_draft=True)`` on the queryset.

If you save an extension the corresponding page is marked as having unpublished changes. To see your extension live make sure to publish the page.

Unfortunately there isn't the possibilty to hook your extension straight in the page admin at the moment.


Advices
=======

If you want the extension to show up in the menu e.g. if you had created an extension that added an icon to the page use MenuModifiers. Every node.id corresponds to their related page.id. ``Page.objects.get(pk=node.id)`` is the way to get the page object. Every page extension has a OneToOne relationship with the page so you can access it by using the reverse relation e.g. ``extension = page.yourextensionlowercased``. Now you can hook this extension by storing it on the node: ``node.extension = extension``. In the menu template you can access your icon on the child object: ``child.extension.icon``. 
