==================
Divio Website 2017
==================


Setup
=====

The project is hosted on the `Divio Cloud <https://control.divio.com/control/2820/edit/28369/>`_.
It can be replicated locally using the `Divio App <https://www.divio.com/en/products/divio-app/>`_
or the command-line tool `Divio CLI <https://github.com/divio/divio-cli>`_:

* ``pip install divio-cli``
* ``divio login``
* ``divio project setup hotelcard``


Frontend
========

Node / NPM
----------

To speed up local building of npm dependencies run:

* ``docker-compose run --rm web /app/tools/build/cache_node_modules.sh``

So from now on, instead of:

* ``docker-compose build web``

do:

* ``docker-compose build web && docker-compose run --rm web /app/tools/build/cache_node_modules.sh``

The first build will still be slow. But all following builds will be
faster. To drop the cache delete ``.cache.node_modules.tar.gz`` and rebuild.
