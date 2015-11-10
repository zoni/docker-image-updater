Docker image updater
====================

*A utility to update docker images automatically. Supports execution of
arbitrary commands when an image is updated, in order to restart running
containers or trigger other custom behaviour.*

.. image:: https://travis-ci.org/zoni/docker-image-updater.svg?branch=master
    :target: https://travis-ci.org/zoni/docker-image-updater
.. image:: https://coveralls.io/repos/zoni/docker-image-updater/badge.svg?branch=master
    :target: https://coveralls.io/r/zoni/docker-image-updater


Installation
------------

Docker image updater can be installed from the
`Python Package Index <https://pypi.python.org/pypi/docker-image-updater>`_
using::

    pip install docker-image-updater

Installation into a `virtualenv <https://virtualenv.pypa.io/en/latest/>`_
is highly recommended!


Usage
-----

::

    usage: docker-image-updater [-h] [-f FILE] [--debug] [file [file ...]]

    positional arguments:
      file                  configuration file(s) to use

    optional arguments:
      -h, --help            show this help message and exit
      -f FILE, --file FILE  deprecated - this flag will be removed in the future
      --debug               show debug messages


Docker image updater requires one or more configuration files which specify
sets of images to watch and commands to execute. By default it will look
for `/etc/docker-image-updater.yml` but you may give one or more alternate
files on the command-line.

When specifying more than one configuration file, the settings will be
merged together with items from the latter configuration file(s) overwriting
items from earlier files.

Recommended usage is to run docker image updater from cron, using
something like `cronic <http://habilis.net/cronic/>`_ to receive mail
only in case of errors.


Example output
--------------

::

    # docker-image-updater
    22:13:04 INFO     Updater    Checking images in set jenkins
    22:13:04 INFO     Updater    Updating image zoni/jenkins
    22:13:04 INFO     Updater    Pulling image zoni/jenkins
    ...........................................................................................................................................................................................................................................................................................................................
    22:14:50 INFO     Updater    Image zoni/jenkins updated to latest version
    22:14:50 INFO     Updater    Running command: supervisorctl restart jenkins
    jenkins: stopped
    jenkins: started
    22:14:54 INFO     Updater    Command exited successfully


Configuration format
--------------------

Configuration is expressed through a YAML file such as the following:

::

    config:
      docker:
        base_url: "unix://var/run/docker.sock"
        version: "1.16"
    watch:
      my-app:
        images:
         - my-app
         - redis
        commands:
         - restart my-app

The item `watch` defines sets of images to watch. This is a dictionary where
the keys (`my-app` in the example above) are arbitrary values for human
reference. Under each of these keys a dictonary with the items `images` and
`commands` is expected.

`images` defines a list of docker images to check for updates. You can
specify these as `image:tag` or simply as `image`, in which case Docker will
use the *latest* tag automatically.

`commands` defines a list of shell commands to execute whenever one of the
listed images was updated. These will be run sequentially, in order.

All items under `config.docker` are passed to the Docker client.
For supported options, refer to the
`docker-py documentation <http://docker-py.readthedocs.org/en/latest/api/>`_.


Exit codes
----------

Docker image updater will exit with status 0 when everything went well,
and there were either no updates or images were updated and all defined
commands returned status code 0.

If an image fails to update or one or more defined commands exits with
a non-zero exit status then docker image updater will itself exit with
status 1.


Star me
-------

If you use this software, please consider
`starring <https://github.com/zoni/docker-image-updater/stargazers>`_
it on GitHub. This will give me some idea of how much it is used by
other people.


Related projects
----------------

* `docker-puller <https://github.com/glowdigitalmedia/docker-puller>`_
* `DockerHub Webhook Listener <https://github.com/cpuguy83/dockerhub-webhook-listener>`_


Changes
-------

1.0.0 (2015-11-10)
~~~~~~~~~~~~~~~~~~

* Allow multiple configuration files to be specified (settings will be merged in order)
* Deprecated the `--file` argument
* Print friendlier error messages in many cases of incorrect configurations

0.0.2 (2015-03-02)
~~~~~~~~~~~~~~~~~~

* Friendlier config file load error message
* Change default config to `/etc/docker-image-updater.yml`

0.0.1 (2015-03-01)
~~~~~~~~~~~~~~~~~~

* Initial public release.


License
-------

The MIT License (MIT)

Copyright (c) 2015 Nick Groenen <nick@groenen.me>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
