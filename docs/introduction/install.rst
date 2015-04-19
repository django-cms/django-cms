#####################
Installing django CMS
#####################

We'll get started by setting up our environment.

************************
Your working environment
************************

We're going to assume that you have a reasonably recent version of virtualenv
installed and that you have some basic familiarity with it.


Create and activate a virtual env
*********************************

::

    virtualenv env
    source env/bin/activate

Note that if you're using Windows, to activate the virtualenv you'll need::

    env\Scripts\activate

Use the django CMS installer
****************************

The `django CMS installer <https://github.com/nephila/djangocms-installer>`_ is
a helpful script that takes care of setting up a new project.

Install it::

    pip install djangocms-installer

This provides you with a new command, ``djangocms``.

Create a new directory to work in, and cd into it::

    mkdir tutorial-project
    cd tutorial-project

Run it to create a new Django project called ``mysite``::

    djangocms -p . mysite

.. warning:: djangocms-installer expects directory ``.`` to be empty at this stage, and will
             check for this, and will warn if it's not.
             You can get it to skip the check and go ahead anyway using  the ``-s`` flag;
             **note that this may overwrite existing files**.


Windows users may need to do a little extra to make sure Python files are associated correctly if that doesn't work right away::

    assoc .py=Python.file
    ftype Python.File="C:\Users\Username\workspace\demo\env\Scripts\python.exe" "%1" %*


For the purposes of this tutorial, it's recommended that you answer the
installer's questions as follows - where our suggestions differ from the
default, they're highlighted below:

* Database configuration (in URL format): sqlite://localhost/project.db
* django CMS version: stable
* Django version: **1.6**
* Activate Django I18N / L10N setting: yes
* Install and configure reversion support: yes
* Languages to enable. Option can be provided multiple times, or as a comma separated list: **en, de**
* Optional default time zone: America/Chicago:
* Activate Django timezone support: yes
* Activate CMS permission management: yes
* Use Twitter Bootstrap Theme: **yes**
* Use custom template set: no
* Load a starting page with examples after installation: **yes**

Create a Django admin user when invited.

Start up the runserver
**********************

::

    python manage.py runserver

Open http://localhost:8000/ in your browser, where you should be presented with
your brand new django CMS homepage.

Congratulations, you now have installed a fully functional CMS!

To log in, append ``?edit`` to the URL and hit enter. This will enable the
toolbar, from where you can log in and manage your website. Switch to ``Draft``
mode to add and edit content.

Try to switch between ``Live`` and ``Draft`` view, between ``Structure`` and
``Content`` mode, add plugins, move them around and delete them again.

To add a *Text* or or other plugin elements to a placeholder:

#.  switch to ``Structure`` mode
#.  select the menu icon on the placeholder's title bar
#.  select a plugin type to add
