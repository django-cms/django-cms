.. versionadded:: 3.0

##########
Page Types
##########

We are introducing "Page Types" to make it easier for content editors to create
pages from predefined presets. This presets contain example plugins and content
that will be carried over the the designated page while leaving the preset
untouched.


*******************
Creating Page Types
*******************

First you need to create a new page through **Add page** from the **Page**
menu that should serve as your preset.

Use this page as your template to add example content and plugins until you
reach a satisfied result.

Once ready, choose **Save as Page Type...** from within the **Page** menu and
give it an appropriate name. Don't worry about the state too much, you can
still change the content and settings later on.

This will create a page type and makes it selectable from within the
**Add Page** and **Create** wizard dialog.

.. image:: /contributing/images/add-page-type.png
   :alt: Creating a page type


*********************
Selecting a Page Type
*********************

You can now select a page type when choosing **Add Page > New Page** from the
**Page** menu. There will be a dropdown named **Page Type** where predefined
page types are selectable.

The same behaviour also occurs within the *Content Creation Wizard* when
selecting **Create > New Page**.

.. image:: /contributing/images/select-page-type.png
   :alt: Selecting a page type


*******************
Managing Page Types
*******************

Page types are added to the page menu and can be organised from the **Pages...**
menu. They will appear underneath the "Page Types" node.

This node behaves different than regular pages:

- They are not publicly accessible
- All pages listed beneath "Page Types" will be rendered in the **Page Types**
  dropdown

All other options, such as remove, copy and add will behave similar to all other
page nodes.
