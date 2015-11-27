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
   :alt: Create new person
   :width: 400
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


*********************
Create an **apphook**
*********************

We now have some people in the system, the next job is to display them - and we want to display them
*automatically*, because we want to do less work, not more.

By default, a django CMS page's content comes from the plugins you insert into it, but if an
application has a django CMS apphook, this application can insert content into your page
automatically.

We'll create a *People* page, and add an apphook for the Aldryn People application to it.

.. todo:: write up steps properly

1. Create new page called People

.. image:: /user/tutorial/images/create_people_page.png
   :alt: Create new person
   :width: 600
   :align: center

2. Select advanced settings

.. image:: /user/tutorial/images/select_advanced_settings.png
   :alt: Create new person
   :width: 150
   :align: center

3. Add Apphook

.. image:: /user/tutorial/images/select_people_app.png
   :alt: Create new person
   :width: 600
   :align: center

4. Publish page

.. image:: /user/tutorial/images/publish_page.png
   :alt: Create new person
   :width: 400
   :align: center

5. View page with automatic list of people in it

.. image:: /user/tutorial/images/people_page_list.png
   :alt: Create new person
   :width: 500
   :align: center

