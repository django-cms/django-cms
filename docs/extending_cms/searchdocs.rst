#########################
Search and the Django-CMS
#########################

Currently the best way to integrate search with the Django-CMS is `Haystack`_,
however it is not officially supported.

.. _Haystack: http://haystacksearch.org/


********
Haystack
********

If you go the Haystack way, you'll need a ``search_indexes.py``.　Haystack
doesn't care if it's in the same app as the models, so you can put it into any
app within your project.

Here is an example **untested** and **unsupported** ``search_indexes.py``:

.. literalinclude:: ../src/haystack.py
