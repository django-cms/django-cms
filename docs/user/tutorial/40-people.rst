#########################
Adding people to the site
#########################

In this section we will add some people to the website using the *Aldryn People* application.

Aldryn People is not part of django CMS, it's a separate application, that is designed to integrate
with it and extend its functionality. It adds new concepts (of people and groups of people) to
django CMS.

We can define some basic attributes that people have, that we'd like to publish information about.

For example, everyone who works in an office will have a name, and probably also has a *role*, and
*email address*, a *phone number* and so on. So we can structure the information that we keep about
people.

django CMS simply handles *content*, but Aldryn People handles and publishes *structured
information*.

You could simply list some information about staff in a django CMS Text plugin, but:

* if you wanted to display that information in another place on the site, you'd have to re-enter it
* if something like a phone number changes, you'll have to find every place you entered it to
  ensure the whole site's up-to-date

So it's much better to record such information just once in an application designed to store that
it, and re-use it wherever it's required. That's what Aldryn People is for.


******************
Create some people
******************

To create a new Person:

#.  Hit **Create**
#.  Select *New Person*.
#.  Hit **Next**.
#.  Enter some details about the person.

    .. tip::

        Name
            Freda Meyer

        Role
            Chief bicycle technician

        Description
            Freda oversees all technical activities in our workshop.

    .. image:: /user/tutorial/images/create_new_person.png
       :alt: Create a new Person
       :width: 600
       :align: center

#.  Hit **Create**.

Do the same for a second person:

.. tip::

    Name
        Cyrus Henrik

    Role
        Bicycle rescue team leader

    Description
        Cyrus is on call night and day to rescue stranded cyclists.

.. _create_an_apphook:

*********************
Create an **apphook**
*********************

We now have some people in the system, the next job is to display them - and we want to display them
*automatically*, because we want to do less work, not more.

By default, a django CMS page's content comes from the plugins you insert into it, but if an
application has a django CMS apphook, this application can insert content into your page
automatically.

We'll create a *People* page, and add an apphook for the Aldryn People application to it.

#.  Create new page called ``People``.

    .. image:: /user/tutorial/images/create_people_page.png
       :alt: Create a new page called 'People'
       :width: 600
       :align: center

#.  Hit **Create**.

#.  In the toolbar, select *Page* > *Advanced settings...*

    .. image:: /user/tutorial/images/select_advanced_settings.png
       :alt: Select 'Advanced settings...'
       :width: 150
       :align: center

#.  In the *Advanced settings*, select the *Application* field and from the menu of options, choose
    *People*. This will 'hook' the People application into this page.

    .. image:: /user/tutorial/images/select_people_app.png
       :alt: Select 'People' from the 'Application' menu
       :width: 600
       :align: center

#.  **Save** the page settings.

    .. |publish-changes| image:: /user/tutorial/images/publish_changes.png
       :alt: 'Publish changes'

#.  Hit |publish-changes| to publish the page.

    .. image:: /user/tutorial/images/people_page_list.png
       :alt: the People page list
       :width: 500
       :align: center


******************
Create a Group
******************

Let's improve the list of People by putting them in a Group (a Group corresponds to a company
department or section, for example).

#.  From the toolbar, select *People* > *Add new Group*.

    .. image:: /user/tutorial/images/add_new_group_toolbar.png
       :alt: Add new group
       :align: center


#.  Provide a *Name* for the group, and if you like, some optional additional information.

    .. image:: /user/tutorial/images/add_group_name.png
       :alt: Add new group title
       :align: center

#.  **Save** the Group.

Now you can add your People to this Group:

#.  From the toolbar, select *People* > *Person list*.

    .. image:: /user/tutorial/images/assign_group_toolbar.png
       :alt: Assign group - Toolbar
       :align: center

#.  Select a Person to edit, and choose the Group to which they belong.

    .. image:: /user/tutorial/images/choose_groups.png
       :alt: Choose groups
       :align: center

#.  **Save**

Note that a Person can be a member of multiple Groups if required.

And here is the published page, with the newly-created group.

    .. image:: /user/tutorial/images/mechanics_people_group.png
       :alt: People page list, with a group
       :align: center
