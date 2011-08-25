############
Installation
############

This guide is a "quick and dirty" way to get the CMS installed and running 
on three different operating systems. To fully understand what you are doing
and what other changes you can make, please read the official docs 
`official_documentation`_.

Please read the documentation fully before logging any problems as you need
to make sure you follow every step.


For the sake of this quick introduction to Django CMS we are using a basic
sqlite3 database, this is not recommended in production environments, for further
database information, please check the bottom of this tutorial.


**********
Virtualenv
**********

The following introduction to virtualenv was written on a Linux machine, however the commands
are very simmilar on Windows and Mac OS X.

Virtualenv creates a virtual python environment. Where you can install packages
without the need to sudo every command (this makes it a lot safer). It also
isolates the packages you install inside your virtualenv, so you cant potentially
damage your system. You can have as many virtual environments as you like, very handy 
if you need to have multiple version of applications on your system.

Virtualenv is not a requirement of the CMS, but it is **very** good practice to use it
and a lot of issues users have, is a result of not using virtualenv. So for this guide,
we will give you a quick and dirty example on how to use it. please read the official docs 
`official_documentation_virtualenv`_.

Configuration
============

.. code-block:: bash  

  $ virtualenv --no-site-packages virt2


Creates a fresh virtualenv called virt2, we use the --no-site-packages to create
a "clean" virtualenv, with no packages pre installed.

Now we have a virtualenv installed, we need to activate it, simply with

.. code-block:: bash 

  $ source virt2/bin/activate


Your prompt on Linux (others may be different) should now look like:

.. code-block:: bash 

  (virt2)$ 


To stop the virtualenv at any time just type
 
.. code-block:: bash 

  $ deactivate


That's it, you are now inside a virtualenv, that's contains no other packages. We
can now use the following commands to get the CMS up and running.

*****
Linux 
*****

Although all three instruction sets use virtualenv, I am only going to explain it
once, here inside the Linux section (saves on screen space)

Make Sure Python is configured
------------------------------

Linux: This guide assumes Ubuntu 11.04

First we need to make sure python is up and running:

.. code-block:: bash 

  $ sudo aptitude install python2.6 python-setuptools python-imaging python-pip python-dev build-essential 


Now we need to install virtualenv 

.. code-block:: bash 

  $ sudo pip install virtualenv
  $ virtualenv --no-site-packages virt2
  $ source virt2/bin/activate


To stop the virtualenv at any time just type 

.. code-block:: bash 

  $ deactivate


Installing django CMS
---------------------

.. code-block:: bash 

  $ pip install django==1.3 south
  $ pip install django-cms
  $ django-admin.py startproject mycmsproject
  $ cd mycmsproject
  $ rm settings.py
  $ rm urls.py
  $ wget https://gist.github.com/raw/1125918/settings.py
  $ wget https://gist.github.com/raw/1125918/urls.py
  $ mkdir templates
  $ cd templates
  $ wget https://gist.github.com/raw/1125918/example.html
  $ cd ..
  $ python manage.py syncdb --all
  $ python manage.py migrate --fake
  $ python manage.py runserver


*******
Windows
*******

This was tested on a Window 7 machine, but to my knowledge there is no reason why it should
not run on Vista or XP.

Windows is NOT the easiest platform to develop django on, but this guides is an attempt to
try and help those users who wish to use Windows.

Make Sure Python is configured
------------------------------

First of we need to get python installed, head over to python.org and download the
latest executable and install it. Version 2.7 is ideal for this guide. Check it
worked after you have installed it by opening the command prompt up and typing:

.. code-block:: bash 

  > cd C:\Python27\           #This assumes you installed to the default location
  > python.exe


If this loads a python prompt, job done. If not, you need to figure out why. There
are plenty of "python on Windows" guides out there, this is just another very basic 
example of one to get the CMS up and running in windows.

Virtualenv
==========

Now we need to download and setup virtualenv. Download it from:

http://pypi.python.org/pypi/virtualenv

Note, the file is a tar.gz, so will need a program like Win-Rar or 7zip (both free)
to open it. Once you have downloaded the file, extract it into C:\Python27 (or where ever python
is installed)

Now from the command prompt

.. code-block:: bash 

  > cd : C:\Python27
  > python.exe "C:\Python27\virtualenv-1.6.4\virtualenv.py" virt2 --no-site-packages


That command assumes virtualenv version 1.6.4 and that we are creating
a virtualenv called "virt2"

Once that command has run, you should see:

.. code-block:: bash 

  New python executable in virt2\Scripts\python.exe
  Installing setuptools...............................done.


Now we need to activate virtualenv

.. code-block:: bash 

  > Scripts\activate.bat

(to deactivate it at any time, simply run "Scripts\deactivate.bat")

Installing django CMS
---------------------

Now we install the files, from this stage on the instructions are very similar to those described
in the Linux section of this tutorial.

.. code-block:: bash 

  > pip install django==1.3 south
  > pip install django-cms


Now we need to setup PIL

You can try

.. code-block:: bash 

  > pip install PIL


If that works, you're good. PIL is notoriously hard to setup on Windows, and you normally need
to install Visual Studio 2008 (its free) make sure its the 2008 version, not the 2010 version.

You can also try (outside of the virtualenv)

.. code-block:: bash
 
  > Scripts\easy_install.exe pil


Both methods are reported to work, however this guide was tested with both methods as we couldn't
get either one working on its own. So you may have to-do both. There is lots of support on the
Internet about running PIL on Windows, so if you are stuck, take a look through Google,
or the python support forums.

Right now we have everything we need to setup the CMS, lets start by creating a django application.

.. code-block:: bash 

  > python Scripts\django-admin.py startproject mycmsproject
  > cd mycmsproject
  > del settings.py
  > del urls.py


Now download new files, and save them into your "mycmsproject" folder, the easiest way is to
download with your browser, and copy and paste them into "mycmsproject" folder

https://gist.github.com/raw/1125918/settings.py
https://gist.github.com/raw/1125918/urls.py

Now we need to create a templates folder where all our templates will be stored, todo this run

.. code-block:: bash 

  > mkdir templates


And download into that directory 

https://gist.github.com/raw/1125918/example.html

Now three commands and we are done:

.. code-block:: bash 

  > python manage.py syncdb --all
  > python manage.py migrate --fake
  > python manage.py runserver


*********
Max OS X
*********

Please note, the Mac OS X installation requires Apple Developer tools, this is free to download
from the appstore. Please see the Linux installation section for information about virtualenv.
The Mac OS X commands are almost identical to the Linux installation instructions you **need** to
read them first before blindly copying + pasting them into a terminal window. Pyton is shipped with 
the base of Mac OS X, so we dont need to install or configure python, it just works.

Virtualenv
==========

First up, lets open a terminal

.. code-block:: bash 

  $ sudo easy_install -U pip
  $ sudo pip PIL virtualenv
  $ virtualenv --no-site-packages virt2
  $ source virt2/bin/activate


To deactivate the virtualenv at any time, type 

.. code-block:: bash 

  $ deactivate


Installing django CMS
---------------------

Now once inside your virtualenv

.. code-block:: bash 

  $ pip install django==1.3 south django-cms PIL
  $ django-admin.py startproject mycmsproject
  $ cd mycmsproject
  $ rm settings.py
  $ rm urls.py
  $ curl -OL https://gist.github.com/raw/1125918/settings.py
  $ curl -OL https://gist.github.com/raw/1125918/urls.py
  $ cd templates
  $ curl -OL https://gist.github.com/raw/1125918/example.html
  $ cd ..
  $ python manage.py syncdb --all
  $ python manage.py migrate --fake
  $ python manage.py runserver


*********
Databases
*********

We recommend using `PostgreSQL`_ or `MySQL`_ with django CMS. Installing and
maintaining database systems is outside the scope of this documentation, but is
very well documented on the system's respective websites. And in the 
`official_documentation_database`_.

To use django CMS efficiently, we recommend:

* Create a separate set of credentials for django CMS.
* Create a separate database for django CMS to use.

.. _PostgreSQL: http://www.postgresql.org/
.. _MySQL: http://www.mysql.command

***********
Conclusion
***********

This is a very basic introduction and is not recommended for production environments,
for further reading please read:

* http://docs.python.org/tutorial/
* https://docs.djangoproject.com/en/1.3/intro/tutorial01/
* http://pypi.python.org/pypi/virtualenv
* http://south.aeracode.org/docs/
* http://docs.django-cms.org/

Now enjoy your new, shiny, pony powered CMS.

.. _official_documentation: http://docs.django-cms.org/
.. _official_documentation_virtualenv: http://pypi.python.org/pypi/virtualenv
.. _official_documentation_database: https://docs.djangoproject.com/en/1.3/topics/install/#database-installation


