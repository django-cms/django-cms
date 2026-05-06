.. _install-docker-production:

Install django CMS with Docker
==============================

The django CMS quickstart project is a Docker-based production-ready setup. If
you know your way around Docker, you will be able to quickly set up a project
that is ready for deployment.

For a simpler local setup without Docker, see :doc:`/introduction/01-install`.

Prerequisites
-------------

Install Docker from `docker.com <https://docs.docker.com/get-docker/>`_. If you
have not used Docker before, read the `Docker getting started guide
<https://docs.docker.com/get-started/>`_.

Setup
-----

Open a terminal and navigate to your projects folder:

.. code-block:: bash

    git clone git@github.com:django-cms/django-cms-quickstart.git
    cd django-cms-quickstart
    docker compose build web
    docker compose up -d database_default
    docker compose run web python manage.py migrate
    docker compose run web python manage.py createsuperuser
    docker compose up -d

Visit http://localhost:8000/admin and log in with your superuser credentials.

The quickstart project
----------------------

The `quickstart project
<https://github.com/django-cms/django-cms-quickstart/tree/support/cms-4.1.x>`_
is a minimal Django project with production-ready defaults including:

- PostgreSQL database configuration
- Static and media file handling
- Production-ready settings structure
- Docker Compose configuration for development and production

For more details, see the `quickstart repository README
<https://github.com/django-cms/django-cms-quickstart>`_.

Creating pages
--------------

Once logged in:

1. Press **Create** on the top right
2. Select **New Page** and press **Next**
3. Add a title and content, then click **Create**
4. Press **Publish** to make the page visible

.. image:: /introduction/images/create_page_with_django_cms1.png
    :alt: Create a page wizard
    :width: 400
    :align: center

Next steps
----------

- Continue with the :doc:`/introduction/index` to learn django CMS development
- See :doc:`/how_to/23-manual-installation` to understand the configuration in detail
