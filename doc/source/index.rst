.. BACpypes documentation master file

Welcome to BACpypes
===================

BACpypes library for building BACnet applications using Python.  Installation 
is easy, just::

    $ sudo easy_install bacpypes

You will be installing the latest released version.  You can also check out
the latest version from SourceForge::

    $ svn checkout https://svn.code.sf.net/p/bacpypes/code/trunk bacpypes

And then use the setup utility to install it::

    $ cd bacpypes/trunk/
    $ python setup.py install

If you would like to participate in its development, please join the
`developers mailing list <https://lists.sourceforge.net/lists/listinfo/bacpypes-developers>`_
and use the `Trac <https://sourceforge.net/apps/trac/bacpypes>`_ to create 
tickets and monitor the project development.  There is also a
`Google+ <https://plus.google.com/100756765082570761221/posts>`_ page that you
can add to your circles have have release notifications show up in your
stream.

For an overview of the current project activity, there is a 
`Trello <https://trello.com/board/bacpypes/4ea6038072bf960d4b036f34>`_ board,
feel free to become a member and share what you are doing with the
rest of the BACpypes community.

Welcome aboard!

Getting Started
---------------

This section is a walk through of the process of installing the library, 
downloading the sample code and communicating with a test device.

.. toctree::
    :maxdepth: 1

    gettingstarted/gettingstarted001.rst
    gettingstarted/gettingstarted002.rst

Tutorial
--------

This tutorial is a step-by-step walk through of the library describing the
essential components of a BACpypes application and how the pieces fit together.

.. toctree::
    :maxdepth: 1

    tutorial/tutorial001.rst
    tutorial/tutorial002.rst
    tutorial/tutorial003.rst
    tutorial/tutorial004.rst
    tutorial/tutorial006.rst

Samples
-------

The library has a variety of sample applications, some of them are a framework
for building larger applications, some of them are standalone analysis tools 
that don't require a connection to a network.

.. toctree::
    :maxdepth: 1

    samples/sample001.rst
    samples/sample002.rst
    samples/sample003.rst
    samples/sample004.rst
    samples/sample005.rst
    samples/sample014.rst

Modules
-------

This documentation is intended for BACpypes developers.

.. toctree::
    :maxdepth: 1

    modules/index.rst

Glossary
--------

.. toctree::
    :maxdepth: 2

    glossary.rst

Release Notes
-------------

.. toctree::
    :maxdepth: 1

    releasenotes.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

