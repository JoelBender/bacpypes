.. BACpypes documentation master file

Welcome to BACpypes
===================

BACpypes library for building BACnet applications using Python.  Installation 
is easy, just::

    $ sudo easy_install bacpypes
    or
    $ sudo pip install bacpypes
    

You will be installing the latest released version from PyPI (the Python Packages Index), 
located at pypi.python.org

.. note::

    You can also check out the latest version from GitHub::
    
        $ git clone https://github.com/JoelBender/bacpypes.git
    
    And then use the setup utility to install it::
    
        $ cd bacpypes
        $ python setup.py install


.. tip::

    If you would like to participate in its development, please join:
    
    - the `developers mailing list <https://lists.sourceforge.net/lists/listinfo/bacpypes-developers>`_,
    - the `chat room on Gitter <https://gitter.im/JoelBender/bacpypes>`_, and 
    - add `Google+ <https://plus.google.com/100756765082570761221/posts>`_ to your circles to have release notifications show up in your stream.


**Welcome aboard!**

------


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
    tutorial/iocb.rst
    tutorial/capability.rst

Migration
---------

If you are upgrading your BACpypes applications to a newer version there are
guidelines of the types of changes you might need to make.

.. toctree::
    :maxdepth: 1

    migration/migration001.rst

Hands-on Lab
-------------

BACpypes comes with a variety of sample applications.  Some are a framework
for building larger applications.  Some are standalone analysis tools  
that don't require a connection to a network. 

The first samples you should have a look too are located inside the 
`samples/HandsOnLab` folder. Those samples are fully explained in the 
documentation so you can follow along and get your head around BACpypes.

Other less documented samples are available directly in the `samples`
folder.

.. toctree::
    :maxdepth: 1

    samples/sample_index.rst


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

------

Modules
-------

.. tip:: Documentation intended for BACpypes developers.

.. toctree::
    :maxdepth: 1

    modules/index.rst

-----


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

