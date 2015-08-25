.. BACpypes Getting Started 1

Getting Started
===============

Ah, so you are interested in getting started with BACnet and Python.  Welcome 
to BACpypes, I hope you enjoy your journey.  This tutorial starts with some 
just enough of the basics of BACnet to get a workstation communicating with 
another device, installing the library, and downloading and configuring the 
samples applications.

Basic Assumptions
-----------------

Assume that you are a software developer and it is your job to communicate 
with a device from another company that uses BACnet.  Your employer has 
given you a test device and purchased a copy of the standard.  You have 
in your office...

- a development workstation running some flavor of Linux complete with 
  the latest version of Python 2.7 and
  `setup tools <https://pypi.python.org/pypi/setuptools#unix-based-systems-including-mac-os-x>`_.

- a small hub you can plug in your workstation and this misterious device
  and not get distracted by lots of other LAN traffic.

Before getting this test environment set up and you are still connected 
to the internet, install the BACpypes library::

    $ sudo easy_install bacpypes

And while you are at it, get a copy of the project from SourceForge that 
has the library source code, sample code, and this documentation::

    $ svn checkout svn://svn.code.sf.net/p/bacpypes/code/trunk bacpypes

No protocol analysis workbench would be complete without an installed 
copy of `Wireshark <http://www.wireshark.org/>`_::

    $ sudo apt-get install wireshark

Configuring the Workstation
---------------------------

The test device that you have is going to come with some configuration 
information by default and sometimes it is easier to set up the test 
environment with same set of assumtions than come up with a fresh set
from scratch.

*IP Address*
   The device will probably come with an IP address, assume that it 
   is 192.168.0.10, subnet mask 255.255.0.0, gateway address 192.168.0.1.
   You are going to be joining the same network, so pick 192.168.0.11 
   for the workstation address with the same subnet mask.

*Device Name*
   Every BACnet device on a BACnet network has a unique name which 
   is a character string.  There is nothing on a BACnet network that 
   enforces this uniqueness, but it is a real headache for integrators
   when it isn't followed.  You will need to pick a name for your 
   workstation.  My collegues and I use star names so the sample 
   congiuration files will have "Betelgeuse".

*Device Identifier*
   Every BACnet device will have a unique identifier, a 22-bit 
   unsigned non-zero value.  It is critical that this be unique for 
   every device and most large customers will have someone or a 
   group responsible for maintaining device identifiers across the
   site.  Keep track of the device identifier for the test device,
   assume that it is **1000** and you are going to pick **1001** 
   for your workstation.

There are a few more configuration values that you will need, but
you won't need to change the values in the sample configuration file 
until you get deeper into the protocol.

*Maximum APDU Length Accepted*
   BACnet works on lots of different types of networks, from high 
   speed Ethernet to "slower" and "cheaper" ARCNET or MS/TP (a 
   serial bus protocol used for a field bus defined by BACnet).
   For devices to exchange messages they have to know the maximum
   size message the device can handle.

*Segmentation Supported*
   A vast majority of BACnet communications traffic fits in one 
   message, but thre can be times when larger messages are 
   convinient and more efficient.  Segmentation allows larger 
   messages to be broken up into segemnts and spliced back together.
   It is not unusual for "low power" field equipment to not 
   support segmentation.

There are other configuration parameters in the INI file that are
used by other applications, just leave them alone for now.

Updating the INI File
~~~~~~~~~~~~~~~~~~~~~

Now that you know what these values are going to be you can 
configure the BACnet part of your workstation.  Change into the 
samples directory that you checked out earlier, make a copy
of the sample configuration file, and edit it for your site::

    $ cd bacpypes/samples
    $ cp BACpypes~.ini BACpypes.ini

The sample applications are going to look for this file, and you 
can direct them to other INI files on the command line, so it is 
simple to keep multiple configurations.

At some point you will probably running both "client" and "server" 
applications on your workstation, so you will want separate 
configuration files for them.  Keep in mind that BACnet devices 
communicate as peers, so it is not unusual for an application to 
act as both a client and a server at the same time.

UDP Communications Issues
-------------------------

BACnet devices comunicate using UDP rather than TCP.  This is so 
that devices do not need to implement a full IP stack (although 
many of them do becuase they support multiple protocols, including
having embedded web servers).

There are two types of UDP messages; *unicast* which is a message 
from one specific IP address and port to another one, and *broadcast*
which is received and processed by all devices that have the port 
open.  BACnet uses both types of messages and your workstation 
will need to receive both types.

The BACpypes.ini file has an *address* parameter which is an IP 
address in CIDR notation and can be followed by a port number.  For
example, **192.168.0.11/16** specifies both the IP address and the
number of bits in the network portion, which in turn implies a 
subnet mask, in this case **255.255.0.0**.  Unicast messages will 
be sent to the IP address, and broadcast messages will be sent to
the broadcast address **192.168.255.255** which is the network 
portion of the configuration value will all 1's in the host 
portion.

To receive both unicast and broadcast addresses, BACpypes will 
open two sockets, one for unicast traffic and one that only listens 
for broadcast messages.  The operating system will typically not allow two
applications to open the same socket at the same time 
so to run two BACnet applciations at 
the same time they need to be configured with different ports.

The BACnet protocol has port 47808 (hex 0xBAC0) assigned to it 
by the `Internet Assigned Numbers Authority <https://www.iana.org/>`_, and sequentially 
higher numbers are used in many applications.  There are some 
BACnet routing and networking isseus with this, but that is for 
antoher tutorial.

Starting An Application
-----------------------

The simplest BACpypes sample application is the **WhoIsIAm.py**
application.  It can send out Who-Is and I-Am messages and 
displays the results it receives.  What are these things?

As mentioned before, BACnet has unique device identifiers and 
most applications use these identifiers in their configuration 
to know who their peers are.  Once these identifiers are given
to a device they typically do not change, even as the network
topology changes.

BACnet devices use the Who-Is request to translate device 
identifiers into network addresses.  This is very similar to 
a decentralized DNS service, but the names are unsigned 
integers.  The request is broadcast on the network and the 
client waits around to listen for I-Am messages.  The source
address of the I-Am response is "bound" to the device identifier 
and most communications is unicast after that.

First, start up Wireshark on your workstation and a capture 
session with a BACnet capture filter::

    udp and port 47808

You might start seeing BACnet traffic from your test device, 
and if you wait to power it on after starting your capture 
you should see at least a broadcast I-Am message.  By looking 
in the I-Am packet decoding you will see some of its 
configuration parameters that should match what you expected 
them to be.

Now start the application::

    $ python WhoIsIAm.py

You will be presented with a prompt, and you can get help::

    > help

    Documented commands (type help <topic>):
    ========================================
    EOF  buggers  bugin  bugout  exit  gc  help  iam  shell  whois

The details of the commands will be described in the next 
section.

Generating An I-Am
------------------

Now that the application is configured it is nice to see some
BACnet communications traffic.  Just generate an I-Am message::

    > iam

You should see your configuration parameters in the I-Am 
message in Wireshark, this is a "global broadcast" message, so your 
test device will see it but since your test device probably 
isn't looking for you, it will not respond with anything.

Binding to the Test Device
--------------------------

Now to confirm that the workstation can receive the 
messages that the test device sends out, generate a Who-Is 
request.  This one will be "unconstrained" which means that 
every device will respond.  *Do not generate these types of
unconstrained requests on a large
network because it will create a lot of traffic that can 
cause conjestion.*  Here is a Who-Is::

    > whois

You should see the request in Wireshark and the response from 
the device, and then a summary line of the response on the 
workstation.

There are a few different forms of the *whois* command this 
simple application allows and you can see the basic form 
with the help command::

    > help whois
    whois [ <addr>] [ <lolimit> <hilimit> ]

This is like a BNF syntax, the whois command is optionally 
followed by an address, and then optionally followed by a
low limit and high limit.  The most common use of the Who-Is
request is to look for a specific device given its device
identifier::

    > whois 1000 1000

And if the site has a numbering scheme for groups of BACnet 
devices like all those in a specific building, then it is 
common to look for all of them as a group::

    > whois 203000 203099

Every once in a while a contractor might install a BACnet 
device that hasn't been properly configured.  Assuming that
it has an IP address, you can send an unconstrained request 
to the specific device and hope that it responds::

    > whois 192.168.0.10

There are other forms of BACnet addresses used in BACpypes,
but that is a subject of an other tutorial.

What's Next
-----------

The next tutorial will describe the different ways this 
application can be run, and what the commands can tell you
about how it is working.  All of the "console" applications, 
those that prompt for commands, use the same basic 
commands and work the same way.

