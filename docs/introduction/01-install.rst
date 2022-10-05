:sequential_nav: next

.. _install-django-cms-tutorial:

######################
Install django CMS
######################

In this tutorial, we'll take you through the first steps to get you started. You will need to install Docker and you will use your system's terminal.

.. note::
  There are several ways to install django CMS.

  1. You can either set up a project on `Divio Cloud <https://www.django-cms.org/en/blog/2020/07/08/simple-django-cms-installation-with-divio-cloud/>`_, which is fast and useful for people without a technical background and a good starting point to experience the CMS User Interface.

  2. As another option, you can set up the project `using docker <https://www.django-cms.org/en/blog/2021/01/19/how-you-spin-up-a-django-cms-project-in-less-than-5-minutes/>`_. It is a good way for a developer locally without an external vendor and we use this option in this django CMS demo.

  3. The last option is to install :ref:`django CMS manually by using virtualenv <installation>`. This option is a good way for developers that want to install everything by hand to understand better and have full control.

************************
Install docker
************************

Install docker from `here <https://docs.docker.com/get-docker/>`_.

************************************************
Clone and run the django CMS quickstart project
************************************************

First, open your system's terminal and go to the folder where you want to install django CMS. Then, type the commands below in the terminal. During the installation process, you will be prompted to enter your email address and set a username and password.


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


****************************************
Confirm you can access the login page
****************************************

Once the installation process has finished, open your browser and type `http://localhost:8000/admin <http://localhost:8000/admin>`_. You have successfully installed django CMS, If you can see the login page.

Log in using the username and password you set during the installation process.

.. image:: /introduction/images/login_prompt.png
   :alt: log in through the admin page
   :width: 100%
   :align: center
