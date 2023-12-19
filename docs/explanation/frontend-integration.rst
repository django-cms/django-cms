.. _frontend-integration:

####################
Frontend integration
####################

Generally speaking, django CMS is wholly frontend-agnostic. It doesn't care what your site's
frontend is built on or uses.

The exception to this is when editing your site, as the django CMS toolbar and editing controls
use their own frontend code, and this can sometimes affect or be affected by your site's code.

The content reloading introduced in django CMS 3.5 for plugin operations (when
moving/adding/deleting etc) pull markup changes from the server. This may require a JS widget to be
reinitialised, or additional CSS to be loaded, depending on your own frontend set-up.

For example, if using Less.js, you may notice that content loads without expected CSS after plugin saves.

In such a case, you can use the ``cms-content-refresh`` event to take care of that, by adding something like:

.. code-block:: html+django

    {% if request.toolbar and request.toolbar.edit_mode_active %}
        <script>
        CMS.$(window).on('cms-content-refresh', function () {
             less.refresh();
        });
        </script>
    {% endif %}

after the toolbar JavaScript.
