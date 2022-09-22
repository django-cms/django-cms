:sequential_nav: next

.. _install-django-cms-tutorial:

######################
Installing django CMS
######################

In this django CMS tutorial, we’ll take you through the first four steps to help get you started. This tutorial is using a `demo project <https://github.com/django-cms/django-cms-quickstart>`_ which is a minimal django project with additional requirements in the ``requirements.txt``.

.. note::
  There are several ways to install django CMS.

  1. You can either set up a project on `Divio Cloud <https://www.django-cms.org/en/blog/2020/07/08/simple-django-cms-installation-with-divio-cloud/>`_, which is fast and useful for people without a technical background and a good starting point to experience the CMS User Interface.

  2. As another option, you can set up the project `using docker <https://www.django-cms.org/en/blog/2021/01/19/how-you-spin-up-a-django-cms-project-in-less-than-5-minutes/>`_. It is a good way for a developer locally without an external vendor and we use this option in this django CMS demo.

  3. The last option is to install :ref:`django CMS manually by using virtualenv <installation>`. This option is a good way for developers that want to install everything by hand to understand better and have full control.

*****************************
What you need to get started
*****************************
You will need to install Docker and you will use your system's terminal.

************************
Setup Docker (Step 1)
************************

Install docker from `here <https://docs.docker.com/get-docker/>`_.

****************************************
Run the demo project in docker (Step 2)
****************************************

First, open the terminal application on your computer and go to a safe folder (e.g. ``cd ~/Projects``), then type the following commands in your system's terminal.

.. note::
   For the commands below, use ``docker compose`` (with a space) if you are using Docker Compose v2. Use ``docker-compose`` (with a hyphen) if you are using Docker Compose v1. For more information, checkout the `Compose v2 Documentation <https://docs.docker.com/compose/#compose-v2-and-the-new-docker-compose-command>`_.

::

      git clone https://github.com/django-cms/django-cms-quickstart.git
      cd django-cms-quickstart
      docker compose build web
      docker compose up -d database_default
      docker compose run web python manage.py migrate
      docker compose run web python manage.py createsuperuser
      docker compose up -d

During the installation process, you will be prompted to enter your email address and set a username and password.

Once the installation process has finished, open your browser and type `http://localhost:8000/admin <http://localhost:8000/admin>`_. There, you should be invited to log in using the username and password you set during the installation process.

.. image:: /introduction/images/admin_page.png
   :alt: log in through the admin page
   :width: 400
   :align: center

********************************
Create your first page (Step 3)
********************************

Once you log in you can press "Create" on the top right corner. Then, you will see a pop-up window with the option “New page” marked in blue.
Press "New Page" and select "Next".

.. image:: /introduction/images/create_page_with_django_cms2.png
   :alt: create a page with django cms
   :width: 400
   :align: center

After selecting "Next", you will be invited to add in your title and some basic content for your new page. Click "Create" after having added the title and the content.

.. image:: /introduction/images/create_page_with_django_cms1.png
   :alt: create a page with django cms
   :width: 400
   :align: center


*********************************
Publish your first page (Step 4)
*********************************

The page we just created is just a draft and needs to be published once you finish.
As an editor, only you can see and edit your drafts, other visitors to your site will only see your published pages.

Press "Publish page now."

.. image:: /introduction/images/django_cms_demo_page.png
   :alt: publish a page with django cms
   :width: 400
   :align: center

To edit the page, you can switch back into editing mode using the "Edit" button, and
return to the published version of the page using the "view published" button.

In the editing mode, you can double-click on the paragraph of the text to change it,
add formatting, and save it again. Any changes that are made after publishing are saved to a draft and will not be visible until you re-publish.

Congratulations, you now have installed django CMS and created your first page.

If you need to log in at any time, append ``?edit`` to the URL and hit Return. This will enable the
toolbar, from where you can log in and manage your website.
