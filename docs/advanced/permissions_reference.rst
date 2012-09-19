###########
Permissions
###########

In django-cms you can set two types of permissions:

1. View restrictions for restricting front-end view access to users
2. Page permissions for allowing staff users to only have rights on certain sections of certain sites

To enable these features, ``settings.py`` requires:

    CMS_PERMISSION = True

*****************
View restrictions
*****************

View restrictions can be set-up from the *View restrictions* formset on any cms page.
Once a page has at least one view restriction installed, only users with granted access will be able to see that page.
Mind that this restriction is for viewing the page as an end-user (front-end view), not viewing the page in the admin interface!

View restrictions are also controlled by the ``CMS_PUBLIC_FOR`` setting. Possible values are ``all`` and ``staff``.
This setting decides if pages without any view restrictions are:

* viewable by everyone -- including anonymous users (*all*)
* viewable by staff users only (*staff*)

****************
Page permissions
****************

After setting ``CMS_PERMISSION = True`` you will have three new models in the admin index:

1. Users (page)
2. User groups (page)
3. Pages global permissions

Using *Users (page)* you can easily add users with permissions over cms pages.

You would be able to create an user with the same set of permissions using the usual *Auth.User* model, but using *Users (page)* is more convenient.

A new user created using *Users (page)* with given page add/edit/delete rights will not be able to make any changes to pages straight away.
The user must first be assigned to a set of pages over which he may exercise these rights.
This is done using the *Page permissions* formset on any page or by using *Pages global Permissions*.

The *Page permission* formset has multiple checkboxes defining different permissions: can edit, can add, can delete, can change advanced settings, can publish, can move and can change permission.
These define what kind of actions the user/group can do on the pages on which the permissions are being granted through the *Grant on* drop-down.

*Can change permission* refers to whether the user can change the permissions of his subordinate users. Bob is the subordinate of Alice if one of:

* Bob was created by Alice
* Bob has at least one page permission set on one of the pages on which Alice has the *Can change permissions* right


**Note:** Mind that even though a new user has permissions to change a page, that doesn't give him permissions to add a plugin within that page.
In order to be able to add/change/delete plugins on any page, you will need to go through the usual *Auth.User* model and give the new user permissions to each plugin you want him to have access to.
Example: if you want the new user to be able to use the text plugin, you will need to give him the following rights: ``text | text | Can add text``, ``text | text | Can change text``, ``text | text | Can delete text``.

Using the *Pages global permissions* model you can give a set of permissions to all pages in a set of sites.

