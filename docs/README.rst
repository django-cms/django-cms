=========================
django CMS Documentation
=========================

Run the documentation locally
-----------------------------

Install the Enchant library
~~~~~~~~~~~~~~~~~~~~~~~~~~

You will need to install the
`enchant <https://www.abisource.com/projects/enchant/>`__ library that
is used by ``pyenchant`` for spelling.

macOS:
^^^^^^

.. code:: bash

    brew install enchant

After that:

Fork & Clone the repository:
^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    git@github.com:your-github-username/django-cms.git

Switch to the django-cms directory:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    cd django-cms/docs

Install the dependencies:
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    make install

This command creates a virtual environment and installs the required
dependencies there.

Start the development server:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    make run

Open the local docs instance in your browser:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    open http://0.0.0.0:8001/

The documentation uses livereload. This means, that every time something
is changed, the documentation will automatically reload in your
browser.

Contribute
----------

If you find anything that could be improved or changed in your opinion,
feel free to create a pull request.
