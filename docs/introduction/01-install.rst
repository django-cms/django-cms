:sequential_nav: next

.. _install-django-cms-tutorial:

######################
Installing django CMS
######################

The setup is incredibly simple, and in this django CMS tutorial, we’ll take you through
the first five steps to help get you started.

*****************************
What you need to get started
*****************************

First of all, you don’t need to be a senior developer or have prior experience as a developer
with Django or Python to create your first django CMS demo website. The added benefit of django CMS, is it’s free.

Before we begin the django CMS tutorial, you will need to know that there are several ways to
install django CMS for free.

1. You can either set up a project on `Divio Cloud <https://www.django-cms.org/en/blog/2020/07/08/simple-django-cms-installation-with-divio-cloud/>`_, which is fast and useful for people without a technical background and a good starting point to experience the CMS User Interface.

2. As another option, you can set up the project `using docker <https://www.django-cms.org/en/blog/2021/01/19/how-you-spin-up-a-django-cms-project-in-less-than-5-minutes/>`_. It is a good way for a developer locally without an external vendor and we use this option in this django CMS demo.

3. The last option is to install :ref:`django CMS manually by using virtualenv <installation>`. This option is a good way for developers that want to install everything by hand to understand better and have full control.

For the sake of this demonstration we will use Option 2, please read on.

************************
Setup Docker (Step 1)
************************

Install docker from `here <https://docs.docker.com/get-docker/>`_

****************************************
Run the demo project in docker (Step 2)
****************************************

Info: The `demo project <https://github.com/django-cms/django-cms-quickstart>`_ is a minimal
django project with some additional requirements in the requirements.txt.

Open the terminal application on your computer and go to a safe folder (i.e. cd ~/Projects), then:


::

      git clone https://github.com/django-cms/django-cms-quickstart.git
      cd django-cms-quickstart
      docker compose build web
      docker compose up -d database_default
      docker compose run web python manage.py migrate
      docker compose run web python manage.py createsuperuser
      docker compose up -d

During the installation process, you will be prompted to enter your email address and set a username and password.
Open your browser and insert ``http://localhost:8000/admin`` there you should be invited to login
and continue with Step 4: create your first page

********************************
Create your first page (Step 3)
********************************

* Once you login you can press Create on the top right.
* Then you will see a pop-up window where the “New page” is marked blue.
* Press New Page and select Next.

.. image:: /introduction/images/create_page_with_django_cms1.png
   :alt: create a page with django cms
   :width: 400
   :align: center


After selecting Next, you will add in your title and some basic text content for the new page,
click Create.

.. image:: /introduction/images/create_page_with_django_cms2.png
   :alt: create a page with django cms
   :width: 400
   :align: center

Here is your newly created page.

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
