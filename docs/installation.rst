Install Dependencies
====================

htsworkflow is written in a way that should be compatible with both
python2 and python3.

If you want to use Postgresql you'll need psycopg2, and if you are
using a virtualenv styal installation, you'll need the postgresql dev
packages for your operating system.

Virtualenv
----------

Useful if you're not on a Linux that provides system packages for the
needed dependencies, or you have some reason to pin the dependency to
a specific version. Unfortunately if you do that, then you're
responsible for making sure all the dependecies are "safe enough."


.. code-block:: bash

   virtualenv -p <python> <virtualenv name>

   source <virtualenv>/bin/activate

   cd htsworkflow
   python setup.py develop
   

Debian
------

Always required dependencies (you can use the python2 version if you
want)

.. code-block:: bash

   python3-django python3-lxml python3-numpy python3-pandas 
   python3-jsonschema python3-requests python3-six python3-rdflib 
   python3-html5lib pytz python3-jsonschema 

Needed for postgresql support

.. code-block:: bash
   
   python3-psycopg2

Needed for running unit tests:

.. code-block:: bash
   
   python3-factory-boy w3c-sgml-lib

Choose a Database
=================

Our production historically used sqlite, but more recent versions of Django
support schema migrations, and the Django project recommends using Postgres 
as that database server best supports migrations.

MySQL or its derivatives probably will work, but are untested.

Web site Installation
=====================

Once you have the dependencies installed and the htsworkflow source tree available
somewhere you'll need to configure it.

The configuration files are in `htsworkflow/settings/*`. There as a
base.py with the default configuration options and a few example host
configurations in felcat.py and production.py.

Information about configuring Django's databases can be found at
https://docs.djangoproject.com/en/dev/topics/install/#database-installation

There's a few settings that are stored in an ini file instead of the
Django settings directory. The primary one is the Django SECRET_KEY

The default search path for the ini file is `~/.htsworkflow.ini`,
`/etc/htsworkflow.ini`.

Make sure an empty file exists in whichever path you'd like to use.

Now if you're using Postgres or MySQL, make sure the database exists
and the user you're running under has access to it.

Once everything is configured you can initialize the database.

.. code:: bash

   python manage.py migrate
   python manage.py createsuperuser

Configure WebServer
===================

As a Django application you'll need a web server that has WSGI support.
We are currently using Apache any WSGI server should work.

Django's instructions should work.

https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/

For Apache you'll need to install mod-wsgi, and enable it.

htsworkflow has a `wsgi.py` driver script in the root of the project.

Here's an example configuration for Apache follows.

.. code:: apache

  RewriteEngine on

  # Configure Django
  WSGIScriptAlias / /<htsworkflow install directory>/wsgi.py
  
  RedirectMatch ^/$ /library/
  Alias /static/admin /<python install directory>/django/contrib/admin/static/admin/
  Alias /static /<htsworkflow install directory>/htsworkflow/frontend/static

Obviously you'll need to replace

 * <htsworkflow install directory> with the path to where you have htsworkflow installed.
 * <python install directory> to the path where django is installed.
   which is likely either your virtualenv, or /usr/lib/python${version}/dist-packages
  
