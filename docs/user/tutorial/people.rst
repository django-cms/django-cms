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

Once more, hit Create, then select *New Person*, followed by **Next**.

Enter some details about the person.

.. tip::

    Name
        Freda Meyer

    Role
        Chief bicycle technician

    Description
        Freda oversees all technical activities in our workshop.

.. todo:: screenshot of above

Hit **Create**.

Do the same for a second person:

.. tip::

    Name
        Cyrus Henrik

    Role
        Bicycle rescue driver

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

We'll create a *People* page, add an apphook for the Aldryn People application to it.

.. todo:: screenshots of following steps (if they are new steps)

.. todo:: write up steps properly

* create new page called People
* add Apphook
* publish page
* view page with automatic list of people in it

.. todo:: discussion of how you can continue to add/edit people


****************************
Rearrange the page structure
****************************

Our menu of pages is growing.

.. todo:: screenshots of menu

As we continue adding pages, we're going to start running out of space. There's room for three, but
there won't be for 30.

The solution is to *nest* pages, in a hierarchy, so that rather than::

    home
    how to find us
    people

it's::

    home
    contact information
        how to find us
        people

.. todo:: screenshots of following steps (if they are new steps)

.. todo:: write up steps properly

* add another new page called "Contact information" and publish it


==============
The Page admin
==============

.. todo:: screenshots of following steps (if they are new steps)

.. todo:: write up steps properly

* view page list in admin
* move "how to find us" and "people" inside "Contact information"
* show result in navigation
* discuss how navigation works
