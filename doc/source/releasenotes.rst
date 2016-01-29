.. BACpypes release notes

Release Notes
=============

This page contains release notes.

Version 0.13.6
--------------

There have been lots of changes in the span between the previous published
version and this one and I haven't quite figured out how to extract the
relevent content from the git log.  More to come.

Version 0.13.0
--------------

This is a big release, with no API changes since the 0.12.1 version, but the
setup now detects which version of Python is running and switches between 
source directories: *py25*, *py27*, and *py34*.

There is now a *test* directory, so in addition to the *build* and *install*
options there is *test*, which uses
`nose <https://nose.readthedocs.org/en/latest/>`_ for running the scripts::

    $ python setup.py test

If you have more than one version of Python installed on your machine you can
use `tox <https://testrun.org/tox/latest/>`_ to run the tests will all of the
supported versions (currently limited to Python2.7 and Python3.4 due to
substantial changes in unittest)::

    $ tox

At some point there will be a documentation page that decribes the changes
between the distributions, as well as a guide for new applications.

Version 0.12.1
--------------

* Add backup-in-progress to the Device Status enumeration
  `r331 <http://sourceforge.net/p/bacpypes/code/331>`_

* Correct the restoreFailure in BackupState
  `r332 <http://sourceforge.net/p/bacpypes/code/332>`_

* Check for read-only object when writing to a file
  `r333 <http://sourceforge.net/p/bacpypes/code/333>`_

* Wrong initial value for no segmentation (old enumeration syntax)
  `r334 <http://sourceforge.net/p/bacpypes/code/334>`_

* Wrong parameter
  `r335 <http://sourceforge.net/p/bacpypes/code/335>`_

* Missed variable name change
  `r336 <http://sourceforge.net/p/bacpypes/code/336>`_

* Mask errors writing the history file like they are when reading
  `r337 <http://sourceforge.net/p/bacpypes/code/337>`_

* Make sure that the vendor identifier is provided, and that localDate and
  localTime are not
  `r338 <http://sourceforge.net/p/bacpypes/code/338>`_

* Add simple string parsing to Date and Time
  `r339 <http://sourceforge.net/p/bacpypes/code/339>`_

* Bump the version number, provide more focused classifiers, include release
  notes
  `r340 <http://sourceforge.net/p/bacpypes/code/340>`_

Version 0.12.0
--------------

* Switch from distutils to setuptools to build a wheel
  `r323 <http://sourceforge.net/p/bacpypes/code/323>`_

* Updated to use twine to upload after building both an egg and a wheel
  `r324 <http://sourceforge.net/p/bacpypes/code/324>`_

* ReallyLongCamelCaseTypo
  `r325 <http://sourceforge.net/p/bacpypes/code/325>`_

* The pieces inside the AtomicReadFileACK should not have been context encoded,
  but the choice is context encoded
  `r326 <http://sourceforge.net/p/bacpypes/code/326>`_

* Additional properties and object types to get closer to 2012 edition
  `r327 <http://sourceforge.net/p/bacpypes/code/327>`_

* Additional properties and enumerations
  `r328 <http://sourceforge.net/p/bacpypes/code/328>`_

* Replace 'except X, T:' with 'except X as T:' for more modern code
  `r329 <http://sourceforge.net/p/bacpypes/code/329>`_

* Bump the version number and include release notes this time
  `r330 <http://sourceforge.net/p/bacpypes/code/330>`_

Version 0.11.0
--------------

* Merge the 0.10.6 release
  `r311 <http://sourceforge.net/p/bacpypes/code/311>`_

* Examples of a RecurringTask and using that to read property values.
  `r312 <http://sourceforge.net/p/bacpypes/code/312>`_

* Minor documentation update, adding --color option
  `r313 <http://sourceforge.net/p/bacpypes/code/313>`_

* IP-to-IP router sample
  `r314 <http://sourceforge.net/p/bacpypes/code/314>`_

* Additional helper application for decoding UDP packet contents in hex
  `r315 <http://sourceforge.net/p/bacpypes/code/315>`_

* The 'description' property is optional, by giving it a default value it was
  always being created.
  `r316 <http://sourceforge.net/p/bacpypes/code/316>`_

* Spelling typo
  `r317 <http://sourceforge.net/p/bacpypes/code/317>`_

* Missing enumerations
  `r318 <http://sourceforge.net/p/bacpypes/code/318>`_

* WhatIsNetworkNumber and NetworkNumberIs decoding (no other support yet)
  `r319 <http://sourceforge.net/p/bacpypes/code/319>`_

* typo
  `r320 <http://sourceforge.net/p/bacpypes/code/320>`_

* reStructured text version of readme
  `r321 <http://sourceforge.net/p/bacpypes/code/321>`_

* Bump the version number
  `r322 <http://sourceforge.net/p/bacpypes/code/322>`_

Version 0.10.6
--------------

* Release notes from previous version.
  `r304 <http://sourceforge.net/p/bacpypes/code/304>`_

* The accessCredential object type was missing.
  `r305 <http://sourceforge.net/p/bacpypes/code/305>`_

* Incorrect number of formatting parameters to match actual parameters, only
  appeared as warnings during debugging, but is definitely annoying.
  `r306 <http://sourceforge.net/p/bacpypes/code/306>`_

* New ReadRange sample code to assist with a developer question, keep them
  coming!
  `r307 <http://sourceforge.net/p/bacpypes/code/307>`_

* The ClientCOV components are not supposed to be context encoded.
  `r308 <http://sourceforge.net/p/bacpypes/code/308>`_

* A change to make sure that an array property isn't None (uninitialized) before
  attempting to index into it.
  `r309 <http://sourceforge.net/p/bacpypes/code/309>`_

* Bump the version number and update these release notes. 
  `r310 <http://sourceforge.net/p/bacpypes/code/310>`_

Version 0.10.5
--------------

* Bill Roberts submitted a patch to clean up an old underscore, and I missed
  the edit earlier.  Thanks Bill!
  `r302 <http://sourceforge.net/p/bacpypes/code/302>`_

* Bump the version number, release notes to come later.
  `r303 <http://sourceforge.net/p/bacpypes/code/303>`_

Version 0.10.4
--------------

This version contains bug fixes.

* Some BACneteer had an issue with MultiState Value Objects so I added some 
  sample code to present one of these on the network so I could check to make
  sure the encoding/decoding of property values was working correctly.

  There was an issue with constructed data with elements that were arrays, 
  the elements should have had Python list semantics rather than BACnet array 
  semantics, so there is some additional checking for this in the 
  decoding.
  `r282 <http://sourceforge.net/p/bacpypes/code/282>`_

* A branch was created for dealing with unicode strings rather than the default 
  string encoding.  No final decision has been made on this issue, I need more 
  experience.
  `r283 <http://sourceforge.net/p/bacpypes/code/283>`_
  `r284 <http://sourceforge.net/p/bacpypes/code/284>`_
  `r285 <http://sourceforge.net/p/bacpypes/code/285>`_
  `r286 <http://sourceforge.net/p/bacpypes/code/286>`_
  `r287 <http://sourceforge.net/p/bacpypes/code/287>`_
  `r289 <http://sourceforge.net/p/bacpypes/code/289>`_
  `r290 <http://sourceforge.net/p/bacpypes/code/290>`_
  `r291 <http://sourceforge.net/p/bacpypes/code/291>`_
  `r292 <http://sourceforge.net/p/bacpypes/code/292>`_

* Delete an unecessary import (a.k.a., "flake").
  `r288 <http://sourceforge.net/p/bacpypes/code/288>`_

* Handle the various combinations of present/missing values for the object 
  identifier and object list keyword arguments to the device object better.
  `r293 <http://sourceforge.net/p/bacpypes/code/293>`_

* The Random Analog Value Object sample code used the object identifier keyword 
  argument in a non-standard way, and I thought this fixed it, but it seems to 
  have re-introduced some debugging code as well.  This needs investigation.
  `r294 <http://sourceforge.net/p/bacpypes/code/294>`_

* For sequences that specify "any atomic value" which is application encoded, 
  the constructed data decoder presents those values as instances of one 
  of the subclasses of Atomic rather that presenting them as Any which needs
  more work decoding for the BACpypes developer.
  `r295 <http://sourceforge.net/p/bacpypes/code/295>`_

* This patch takes advantage of the r295 and applies it to the Schedule Object 
  and the TimeValue, used in SpecialEvent, used in the exception Schedule.
  `r296 <http://sourceforge.net/p/bacpypes/code/296>`_

* In the Read Property sample code, if the value has a debug_contents API 
  then it is called and this gives a little bit more detailed output.
  `r297 <http://sourceforge.net/p/bacpypes/code/297>`_

* New Schedule Object sample code.
  `r298 <http://sourceforge.net/p/bacpypes/code/298>`_

* The fileIdentifier parameter of the Atomic Read/Write File services is 
  application encoded, not context encoded.
  `r299 <http://sourceforge.net/p/bacpypes/code/299>`_

* Bill Roberts submitted some patches to clean up element encoding errors, 
  thank you Bill!
  `r300 <http://sourceforge.net/p/bacpypes/code/300>`_

* Bump the version number and release.  Notes to be committed later.
  `r301 <http://sourceforge.net/p/bacpypes/code/301>`_

Version 0.10.3
--------------

This version contains some enhancements and bug fixes.

* Sangeeth Saravanaraj submitted an enchancement that allows the ConsoleCmd class
  to accept stdin and stdout parameters and replaces the print statements with 
  self.stdout.write calls.  Thank you!
  `r276 <http://sourceforge.net/p/bacpypes/code/276>`_

* This is a new filter that looks for Who-Is and I-Am messages related to a specific
  device instance number in a pcap file.
  `r277 <http://sourceforge.net/p/bacpypes/code/277>`_

* This minor enhancement allows longs in the object type for an object identifier
  ``__init__`` parameter rather than just ints.
  `r278 <http://sourceforge.net/p/bacpypes/code/278>`_

* Application service access point encode and decoding errors bail out of the effort
  rather than raising an error.  There is a very long running application that I have
  that would decode an APDU incorrectly every once in a great while, but it was very
  difficult to track down.  I think this was actually field device that was adding 
  additional cruft on the end of a packet and BACpypes would raise an error.  I need 
  the stack to toss these errant PDUs out as if they never happened.
  It would be nice if there was a logging hook that developers could use to track
  when this happens.
  `r279 <http://sourceforge.net/p/bacpypes/code/279>`_

* This is a pair of sample applications for proprietary object types and proprietary
  properties to demonstrate how to extend the core types.
  `r280 <http://sourceforge.net/p/bacpypes/code/280>`_

* Bump the version number and update these release notes.
  `r281 <http://sourceforge.net/p/bacpypes/code/281>`_

Version 0.10.2
--------------

This version contains bug fixes.

* The invokeID for outbound client requests must be unique per server, but can be
  the same value for different servers.  I had solved this problem once before in the 
  sample HTTP server code, but didn't migrate the code into the core library.  At 
  some point there was some other code that couldn't generate more than 255 requests, so 
  this never got tested.  Other BACneteers are more aggressive!
  `r272 <http://sourceforge.net/p/bacpypes/code/272>`_

* The segment count of a confirmed ack is at least one, even if there is no PDU data.
  This was solved on the client side (in the client segmentation state machine for seeing
  if requests needed to be segmented on the way out) but not on the server side.  This
  fixes that bug.
  `r273 <http://sourceforge.net/p/bacpypes/code/273>`_

* The ReadPropertyMultipleServer code would see that an object didn't exist and build an
  error response, which was oblitered by the default code at the bottom of the loop so 
  it was never returned.  Now if any of the read access specifications refers to an object 
  that doesn't exist the request will correctly return an error.
  `r274 <http://sourceforge.net/p/bacpypes/code/274>`_

* Bump the version number and update these release notes.
  `r275 <http://sourceforge.net/p/bacpypes/code/275>`_

Version 0.10.1
--------------

This version contains more contributions that should have been included in the previous
release, but I updated the library in a different order than the mailing list.  Sigh.

* The library did not return the correct error for writing to immutable properties.
  `r269 <http://sourceforge.net/p/bacpypes/code/269>`_

* The lowerCamelCase for CharacterStringValue objects was incorrect and didn't match
  the enumeration value.
  `r270 <http://sourceforge.net/p/bacpypes/code/270>`_

* Bump the version number and update these release notes.
  `r271 <http://sourceforge.net/p/bacpypes/code/271>`_

Version 0.10
------------

This version contains updates courtesy of contributions from other BACpypes users, of whom 
I am grateful!

* The consolelogging module ConfigArgumentParser inherits from the built-in ArgumentParser
  class, but the parse_args didn't have the same function signature.
  `r264 <http://sourceforge.net/p/bacpypes/code/264>`_

* The MultipleReadProperty new sample application has a list of points and it shows how
  to put those points into a queue so each one of them can be read sequentially.
  `r265 <http://sourceforge.net/p/bacpypes/code/265>`_

* The Read Access and Stream Access choices in the atomic file services were backwards, 
  stream access is choice zero (0) and record access is one (1).
  `r266 <http://sourceforge.net/p/bacpypes/code/266>`_

* In the process of confirming that the file access services were in fact wrong, I decided 
  to update the sample applications and give them better names.
  `r267 <http://sourceforge.net/p/bacpypes/code/267>`_

* Bump the version number and update these release notes.
  `r268 <http://sourceforge.net/p/bacpypes/code/268>`_

Version 0.9.5
-------------

I have been working more on converting PDU's into JSON content that can be archived and searched in 
MongoDB.

* Simple bug, while I was updated in the ``__init__`` calling chain I got the class name wrong.
  `r260 <http://sourceforge.net/p/bacpypes/code/260>`_

* When there is network layer traffic on a port that is not the "local port" it still needs to be
  processed by the local ``NetworkServiceElement``.  And trying to debug this problem, there was 
  no debugger for the NSE!
  `r261 <http://sourceforge.net/p/bacpypes/code/261>`_

* As I have been shuffling around JSON-like content in various applications it became harder and 
  harder to manage if the result of calling ``dict_content`` was going to return PCI layer information
  (the NPCI, APCI, or BVLCI), or the "data" portion of the packet.  I also took the opportunity to 
  use simpler names.
  `r262 <http://sourceforge.net/p/bacpypes/code/262>`_

* Bump the version number and update these release notes.
  `r263 <http://sourceforge.net/p/bacpypes/code/263>`_

Version 0.9.4
-------------

This revision is an annouced release.  The combination of `r258 <http://sourceforge.net/p/bacpypes/code/258>`_
and `r256 <http://sourceforge.net/p/bacpypes/code/256>`_ makes this important to get out
to the community sooner rather than later.

* The ``TimeSynchronizationRequest`` application layer PDUs have their ``time`` parameter
  application encoded, not context encoded.
  `r258 <http://sourceforge.net/p/bacpypes/code/258>`_

* Bump the version number and update these release notes.
  `r259 <http://sourceforge.net/p/bacpypes/code/259>`_

Version 0.9.3
-------------

This release just has some minor bug fixes, but in order to get a large collection of 
applications running quickly it was simpler to make minor release and install it on 
other machines.  The version was release to PyPI but never annouced.

Revisions `r255 <http://sourceforge.net/p/bacpypes/code/255>`_
through `r257 <http://sourceforge.net/p/bacpypes/code/257>`_.

* A simple copy/paste error from some other sample code.
  `r255 <http://sourceforge.net/p/bacpypes/code/255>`_

* When shuffling data around to other applications and databases (like MongoDB) there
  are problems with raw string data, a.k.a., octet strings, or in Python3 terms byte
  strings.  This is a simple mechanism to make hex strings out of the data portion of 
  tag data.  This is subject to change to some other format as we get more experience 
  with data in other applications.
  `r256 <http://sourceforge.net/p/bacpypes/code/256>`_

* Remove the "flakes" (modules that were imported but not used).
  `r257 <http://sourceforge.net/p/bacpypes/code/257>`_

Version 0.9.2
-------------

Apart from the usual bug fixes and small new features, this release changes
almost all of the ``__init__`` functions to use ``super()`` rather than
calling the parent class initializer.

New School Initialization
~~~~~~~~~~~~~~~~~~~~~~~~~

For example, while the old code did
this::

    class Foo(Bar):
    
        def __init__(self):
            Bar.__init__(self)
            self.foo = 12

New the code does this::

    class Foo(Bar):
    
        def __init__(self, *args, **kwargs):
            super(Foo, self).__init__(*args, **kwargs)
            self.foo = 12

If you draw an inheritance tree starting with ``PDUData`` at the top and 
ending with something like ``ReadPropertyRequest`` at the bottom, you will 
see lots of branching and merging.  Calling the parent class directly may 
lead to the same base class being "initialized" more than once which was 
causing all kinds of havoc.

Simply replacing the one with the new wasn't quite good enough however, 
because it could lead to a situation where a keyword arguement needed to be 
"consumed" if it existed because it didn't make sense for the parent class 
or any of its parents.  In many cases this works::

    class Foo(Bar):
    
        def __init__(self, foo_arg=None, *args, **kwargs):
            super(Foo, self).__init__(*args, **kwargs)
            self.foo = 12

When the parent class initializer gets called the ``foo_arg`` will be a 
regular parameter and won't be in the ``kwargs`` that get passed up the 
inheritance tree.  However, with ``Sequence`` and ``Choice`` there is 
no knowledge of what the keyword parameters are going to be without going 
through the associated element lists.  So those two classes go to great 
lengths to divide the kwargs into "mine" and "other".

New User Data PDU Attribute
~~~~~~~~~~~~~~~~~~~~~~~~~~~

I have been working on a fairly complicated application that is a combination 
of being a BBMD on multiple networks and router between them.  The twist is 
that there are rules that govern what segments of the networks can see each 
other.  To manage this, there needed to be a way to attach an object at the bottom 
of the stack when a PDU is received and make sure that context information 
is maintained all the way up through the stack to the application layer and 
then back down again.

To accomplish this there is a ``pduUserData`` attribute you can set and as 
long as the stack is dealing with that PDU or the derived encoded/decoded 
PDUs, that reference is maintained.

Revisions `r246 <http://sourceforge.net/p/bacpypes/code/246>`_
through `r254 <http://sourceforge.net/p/bacpypes/code/254>`_.

* The sample HTTP server was using the old syle argument parser 
  and the old version didn't have the options leading to confusion.
  `r246 <http://sourceforge.net/p/bacpypes/code/246>`_

* Set the 'reuse' flag for broadcast sockets.  A BACneteer has
  a workstation with two physical adapters connected to the same
  LAN with different IP addresses assigned for each one.  Two
  BACpypes applications were attempting to bind to the same 
  broadcast address, this allows that scenerio to work.
  `r247 <http://sourceforge.net/p/bacpypes/code/247>`_

* Fix the help string and add a little more error checking to the
  ReadPropertyMultiple.py sample application.
  `r248 <http://sourceforge.net/p/bacpypes/code/248>`_

* Add the --color option to debugging.  This wraps the output of the 
  LoggingFormatter with ANSI CSI escape codes so the output from 
  different log handlers is output in different colors.  When 
  debugging is turned on for many modules it helps!
  `r249 <http://sourceforge.net/p/bacpypes/code/249>`_

* The WriteProperty method now has a ''direct'' parameter, this 
  fixes the function signatures of the sample applications to include
  it.
  `r250 <http://sourceforge.net/p/bacpypes/code/250>`_

* Change the ``__init__`` functions to use ``super()``, see explanation 
  above.
  `r251 <http://sourceforge.net/p/bacpypes/code/251>`_

* Bump the minor version number.
  `r252 <http://sourceforge.net/p/bacpypes/code/252>`_

* Update the getting started document to include the new color debugging
  option.  There should be more explanation of what that means exactly,
  along with a link to the Wikipedia color code tables.
  `r253 <http://sourceforge.net/p/bacpypes/code/253>`_

* Update these release notes.
  `r254 <http://sourceforge.net/p/bacpypes/code/254>`_

Version 0.9.1
-------------

Most of this release is just documentation, but it includes some new functionality
for translating PDUs into dictionaries.  The new ``dict_contents`` functions will 
most likely have some bugs, so consider that API unstable.

Revisions `r238 <http://sourceforge.net/p/bacpypes/code/238>`_
through `r245 <http://sourceforge.net/p/bacpypes/code/245>`_.

* For some new users of BACpypes, particularly those that were also new to BACnet,
  it can be a struggle getting something to work.  This is the start of a new
  documentation section to speed that process along.
  `r238 <http://sourceforge.net/p/bacpypes/code/238>`_
  `r239 <http://sourceforge.net/p/bacpypes/code/239>`_
  `r240 <http://sourceforge.net/p/bacpypes/code/240>`_

* For multithreaded applications it is sometimes handly to override the default 
  spin value, which is the maximum amount of time that the application should 
  be stuck in the asyncore.loop() function.  The developer could import the 
  core module and change the CORE value before calling run(), but that seems 
  excessively hackish.
  `r241 <http://sourceforge.net/p/bacpypes/code/241>`_

* Apparently there should not be a dependancy on ``setuptools`` for developers that 
  want to install the library without it.  In revision `r227 <http://sourceforge.net/p/bacpypes/code/227>`_
  I changed the setup.py file, but that broke the release script.  I'm not 
  completely sure this is correct, but it seems to work.
  `r242 <http://sourceforge.net/p/bacpypes/code/242>`_

* This revision includes a new dict_contents() function that encodes PDU content
  into a dict-like object (a real ``dict`` by default, but the developer can provide 
  any other class that supports ``__setitem__``).  This is the first step in a long
  road to translate PDU data into JSON, then into BSON to be streamed into a 
  MongoDB database for analysis applications.
  `r243 <http://sourceforge.net/p/bacpypes/code/243>`_

* Bump the version number before releasing it.
  `r244 <http://sourceforge.net/p/bacpypes/code/244>`_

* Update these release notes.
  `r245 <http://sourceforge.net/p/bacpypes/code/245>`_

Version 0.9
-----------

There are a number of significant changes in BACpypes in this release, some of which
may break existing code so it is getting a minor release number.  While this project
is getting inexorably closer to a 1.0 release, we're not there yet.

The biggest change is the addition of a set of derived classes of ``Property`` that
match the names of the way properties are described in the standard; ``OptionalProperty``,
``ReadableProperty``, and ``WritableProperty``.  This takes over from the awkward and
difficult-to-maintain combinations of ``optional`` and ``mutable`` constructor parameters.
I went through the standard again and matched the class name with the object definition
and it is much cleaner.

This change was brought about by working on the `BACowl <http://bacowl.sourceforge.net/>`_
project where I wanted the generated ontology to more closely match the content of the 
standard.  This is the first instance where I've used the ontology design to change 
application code.

Revisions `r227 <http://sourceforge.net/p/bacpypes/code/227>`_
through `r234 <http://sourceforge.net/p/bacpypes/code/234>`_.

* At some point ``setuptools`` was replaced with ``distutils`` and this needed to change
  while I was getting the code working on Windows.
  `r227 <http://sourceforge.net/p/bacpypes/code/227>`_

* Added the new property classes and renamed the existing ``Property`` class instances.
  There are object types that are not complete (not every object type has every property
  defined) and these will be cleaned up and added in a minor release in the near future.
  `r228 <http://sourceforge.net/p/bacpypes/code/228>`_

* The UDP module had some print statements and a traceback call that sent content to stdout,
  errors should go to stderr.
  `r229 <http://sourceforge.net/p/bacpypes/code/229>`_

* With the new property classes there needed to be a simpler and cleaner way managing the
  __init__ keyword parameters for a ``LocalDeviceObject``.  During testing I had created
  objects with no name or object identifier and it seemed like some error checking was
  warrented, so that was added to ``add_object`` and ``delete_object``.
  `r230 <http://sourceforge.net/p/bacpypes/code/230>`_

* This commit is the first pass at changing the way object classes are registered.  There
  is now a new ``vendor_id`` parameter so that derived classes of a standard object can be
  registered.  For example, if vendor Snork has a custom SnorkAnalogInputObject class (derived
  from ``AnalogInputObject`` of course) then both classes can be registered.

  The ``get_object_class`` has a cooresponding ``vendor_id`` parameter, so if a client
  application is looking for the appropriate class, pass the ``vendorIdentifier`` property
  value from the deivce object of the server and if there isn't a specific one defined, the
  standard class will be returned.

  The new and improved registration function would be a lot nicer as a decorator, but optional
  named parameters make and interesting twist.  So depending on the combination of parameters
  it returns a decorator, which is an interesting twist on recursion.

  At some point there will be a tutorial covering just this functionality, and before this
  project hits version 1.0, there will be a similar mechanism for vendor defined enumerations,
  especially ``PropertyIdentifier``, and this will also follow the BACowl ontology conventions.

  This commit also includes a few minor changes like changing the name ``klass`` to the 
  not-so-cute ``cls``, ``property`` to ``propid`` because the former is a reserved word, and 
  the dictionary of registered objects from ``object_types`` to ``registered_object_types``.
  `r231 <http://sourceforge.net/p/bacpypes/code/231>`_

* Simple wrapping of the command line argument interpretation for a sample application.
  `r232 <http://sourceforge.net/p/bacpypes/code/232>`_

* The ``CommandableMixin`` isn't appropriate for ``BinaryValueObject`` type, so I replaced it
  with a ``DateValueObject``.
  `r233 <http://sourceforge.net/p/bacpypes/code/233>`_

* I managed to install Sphinx on my Windows laptop and this just added a build script to make
  it easier to put in these release notes.
  `r235 <http://sourceforge.net/p/bacpypes/code/235>`_

* This adds the relaease notes page and a link to it for documentation, committed so I could
  continue working on it from a variety of different places.  I usually wouldn't make a commit just
  for this unless I was working in a branch, but because I'm working in the trunk rather than 
  using a service like DropBox I decided to let myself get away with it.
  `r234 <http://sourceforge.net/p/bacpypes/code/234>`_
  `r236 <http://sourceforge.net/p/bacpypes/code/236>`_

* Committed the final version of these notes and bumped the minor version number.
  `r237 <http://sourceforge.net/p/bacpypes/code/237>`_

Version 0.8
-----------

Placeholder for 0.8 release notes.

Revisions `r224 <http://sourceforge.net/p/bacpypes/code/224>`_
through `r226 <http://sourceforge.net/p/bacpypes/code/226>`_.

* Placeholder for comments about revision 224.
  `r224 <http://sourceforge.net/p/bacpypes/code/224>`_

* Placeholder for comments about revision 225.
  `r225 <http://sourceforge.net/p/bacpypes/code/225>`_

* Bump the minor version number.
  `r226 <http://sourceforge.net/p/bacpypes/code/226>`_

Version 0.7.5
-------------

Placeholder for 0.8 release notes.

Revisions `r217 <http://sourceforge.net/p/bacpypes/code/217>`_
through `r223 <http://sourceforge.net/p/bacpypes/code/223>`_.

* Placeholder for comments about revision 217.
  `r217 <http://sourceforge.net/p/bacpypes/code/217>`_

* Placeholder for comments about revision 218.
  `r218 <http://sourceforge.net/p/bacpypes/code/218>`_

* Placeholder for comments about revision 219.
  `r219 <http://sourceforge.net/p/bacpypes/code/219>`_

* Placeholder for comments about revision 220.
  `r220 <http://sourceforge.net/p/bacpypes/code/220>`_

* Placeholder for comments about revision 221.
  `r221 <http://sourceforge.net/p/bacpypes/code/221>`_

* Placeholder for comments about revision 222.
  `r222 <http://sourceforge.net/p/bacpypes/code/222>`_

* Bump the patch version number.
  `r223 <http://sourceforge.net/p/bacpypes/code/223>`_

Version 0.7.4
-------------

Lost to the sands of time.

