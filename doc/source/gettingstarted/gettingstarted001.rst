.. BACpypes Getting Started 1

Getting Started
===============

Ah, so you are interested in getting started with BACnet and Python.  Welcome 
to BACpypes, I hope you enjoy your journey.  This tutorial starts with  
just enough of the basics of BACnet to get a workstation communicating with 
another device.  We will cover installing the library, downloading and 
configuring the samples applications.

Basic Assumptions
-----------------

I will assume you are a software developer and it is your job to communicate 
with a device from another company that uses BACnet.  Your employer has 
given you a test device and purchased a copy of the BACnet standard.  I will 
need...

- a development workstation running some flavor of Linux or Windows, complete with 
  the latest version of Python (2.7 or >3.4) and
  `setup tools <https://pypi.python.org/pypi/setuptools#unix-based-systems-including-mac-os-x>`_.

- a small Ethernet hub into which you can plug both your workstation and your 
  mysterious BACnet device, so you won't be distracted by lots of other network traffic.

- a BACnetIP/BACnet-MSTP Router if your mysterious device is an MSTP device (BACpypes is
  actually BACnet/IP software)

- if you are running on Windows, installing Python may be a challenge. Some
  Python packages make your life easier by including the core Python plus
  many other data processing toolkits, so have a look at Continuum Analytics
  `Anaconda <https://www.continuum.io/downloads>`_ or Enthought
  `Canopy <https://www.enthought.com/products/canopy/>`_.

Before getting this test environment set up and while you are still connected 
to the internet, install the BACpypes library::

    $ sudo easy_install bacpypes

or::

    $ sudo pip install bacpypes

And while you are at it, get a copy of the BACpypes project from GitHub.  It 
contains the library source code, sample code, and this documentation.  Install
the `Git <https://en.wikipedia.org/wiki/Git>`_ software from
`here <https://git-scm.com/downloads>`_, then make a local copy of the
repository by cloning it::

    $ git clone https://github.com/JoelBender/bacpypes.git

No protocol analysis workbench would be complete without an installed 
copy of `Wireshark <http://www.wireshark.org/>`_::

    $ sudo apt-get install wireshark
   
or if you use Windows, `download it here <https://www.wireshark.org/download.html>`_.

.. caution::

    Don't forget to **turn off your firewall** before beginning to play
    with BACpypes! It will prevent you from hours of researches when
    your code won't work as it should!


Configuring the Workstation
---------------------------

The mystery BACnet device you have is going to come with some configuration 
information by default and sometimes it is easier to set up the test 
environment with my set of assumptions than come up with a fresh set
from scratch.

*IP Address*
   The device will probably come with an IP address, let's assume that it 
   is 192.168.0.10, subnet mask 255.255.0.0, gateway address 192.168.0.1.
   You are going to be joining the same network, so pick 192.168.0.11 
   for your workstation address and use the same subnet mask 255.255.0.0.

   If working with MSTP devices, base your workstation address on the address
   of the BACnetIP Router.

*Network Number*
   If working with a BACnetIP router and an MSTP device, you will need to know
   the network number configured inside the router. Every BACnet network **must**
   have a unique numeric identifier. You will often see the magical number **2000** 
   but you can choose anything between 1 to 0xFFFE.

*Device Identifier*
   Every BACnet device on a BACnet network **must** have a unique numeric 
   identifier.  This number is a 22-bit unsigned non-zero value.  
   It is critical this identifier be unique.  Most large customers will have 
   someone or some group responsible for maintaining device identifiers across the
   site.  Keep track of the device identifier for the test device.  Let's 
   assume that this device is **1000** and you are going to pick **1001** 
   for your workstation.

*Device Name*
   Every BACnet device on a BACnet network should also have a unique name, which 
   is a character string.  There is nothing on a BACnet network that 
   enforces this uniqueness, but it is a real headache for integrators
   when it isn't followed.  You will need to pick a name for your 
   workstation.  My collegues and I use star names, so in the sample 
   configuration files you will see the name "Betelgeuse".  An actual customer's
   site will use a more formal (but less fun) naming convention. 


There are a few more configuration values that you will need, but
you won't need to change the values in the sample configuration file  
until you get deeper into the protocol.

*Maximum APDU Length Accepted*
   BACnet works on lots of different types of networks, from high 
   speed Ethernet to "slower" and "cheaper" ARCNET or MS/TP (a 
   serial bus protocol used for a field bus defined by BACnet).
   For devices to exchange messages they need to know the maximum
   size message the other device can handle.

*Segmentation Supported*
   A vast majority of BACnet communications traffic fits in one 
   message, but there are times when larger messages are 
   convenient and more efficient.  Segmentation allows larger 
   messages to be broken up into segments and spliced back together.
   It is not unusual for "low power" field devices to not 
   support segmentation.

There are other configuration parameters in the INI file that are
also used by other applications, just leave them alone for now.


Updating the INI File
~~~~~~~~~~~~~~~~~~~~~

Now that you know what these values are going to be, you can 
configure the BACnet portion of your workstation.  Change into the 
samples directory that you checked out earlier, make a copy
of the sample configuration file, and edit it for your site::

    $ cd bacpypes/samples
    $ cp BACpypes~.ini BACpypes.ini

.. tip:: 

    The sample applications are going to look for this file.
    You can direct the applications to use other INI files on the command line, so it is 
    simple to keep multiple configurations.

    At some point you will probably running both "client" and "server" 
    applications on your workstation, so you will want separate 
    configuration files for them.  Keep in mind that BACnet devices 
    communicate as peers, so it is not unusual for an application to 
    act as both a client and a server at the same time.

A typical BACpypes.ini file contains 

    [BACpypes]
    objectName: Betelgeuse
    address: 192.168.1.2/24
    objectIdentifier: 599
    maxApduLengthAccepted: 1024
    segmentationSupported: segmentedBoth
    maxSegmentsAccepted: 1024
    vendorIdentifier: 15
    foreignPort: 0
    foreignBBMD: 128.253.109.254
    foreignTTL: 30


UDP Communications Issues
-------------------------

BACnet devices communicate using UDP rather than TCP.  This is so 
devices do not need to implement a full IP stack (although 
many of them do becuase they support multiple protocols, including
having embedded web servers).

There are two types of UDP messages; *unicast* which is a message 
from one specific IP address (and port) to another device's IP address 
(and port); and *broadcast* messages which are sent by one device 
and received and processed by all other devices that are listening 
on that port.  BACnet uses both types of messages and your workstation 
will need to receive both types.

The BACpypes.ini file has an *address* parameter which is an IP 
address in CIDR notation and can be followed by a port number.  For
example, **192.168.0.11/16** specifies both the IP address and the
number of bits in the network portion, which in turn implies a 
subnet mask, in this case **255.255.0.0**.  Unicast messages will 
be sent to the IP address, and broadcast messages will be sent to
the broadcast address **192.168.255.255** which is the network 
portion of the address with all 1's in the host portion. In this example, 
the default port 47808 (0xBAC0) is used but you could provide and different
one, **192.168.0.11:47809/16**.

To receive both unicast and broadcast addresses, BACpypes  
opens two sockets, one for unicast traffic and one that only listens 
for broadcast messages.  The operating system will typically not allow two
applications to open the same socket at the same time 
so to run two BACnet applciations at 
the same time they need to be configured with different ports.

.. note::

    The BACnet protocol has been assigned port 47808 (hex 0xBAC0) by  
    by the `Internet Assigned Numbers Authority <https://www.iana.org/>`_, and sequentially 
    higher numbers are used in many applications (i.e. 47809, 47810,...).  
    There are some BACnet routing and networking issues related to using these higher unoffical
    ports, but that is a topic for another tutorial.


Starting An Application
-----------------------

The simplest BACpypes sample application is the **WhoIsIAm.py**
application.  It sends out Who-Is and I-Am messages and 
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
and most communications are unicast thereafter.

First, start up Wireshark on your workstation and a capture 
session with a BACnet capture filter::

    udp and port 47808

You might start seeing BACnet traffic from your test device, 
and if you wait to power it on after starting your capture 
you should see at least a broadcast I-Am message.  By looking 
in the I-Am packet decoding you will see some of its 
configuration parameters that should match what you expected 
them to be.

Now start the simplest tutorial application::

    $ python samples/Tutorial/WhoIsIAm.py

.. note::

    The samples folder contains a Tutorial folder holding all the samples
    that you will need too follow along this tutorial.
    Later, the folder `HandsOnLabs` will be used as it contains the samples
    that are fully explained in this document (see table of content)

You will be presented with a prompt (>), and you can get help::

    > help

    Documented commands (type help <topic>):
    ========================================
    EOF  buggers  bugin  bugout  exit  gc  help  iam  shell  whois

The details of the commands are described in the next section.


Generating An I-Am
------------------

Now that the application is configured it is nice to see some
BACnet communications traffic.  Generate the basic I-Am message::

    > iam

You should see Wireshark capture your I-Am message containing your configuration 
parameters.  This is a "global broadcast" message.  Your test device will see
it but since your test device probably isn't looking for you, it will not
respond to the message.


Binding to the Test Device
--------------------------

Next we want to confirm that your workstation can receive the 
messages the test device sends out.  We do this by generating a 
generic Who-Is request.  The request will be "unconstrained", meaning 
every device that hears the message will respond with their corresponding
I-Am messages.  

.. caution:: 

    Generating **unconstrained** Who-Is requests on a large network will create 
    a LOT of traffic, which can lead to network problems caused by the resulting 
    flood of messages.
    
To generate the Who-Is request::

    > whois

You should see the Who-Is request captured in Wireshark along with the I-Am 
response from your test device, and then the details of the response displayed 
on the workstation console.::

    > whois 
    > pduSource = <RemoteStation 50009:9>
    iAmDeviceIdentifier = ('device', 1000)
    maxAPDULengthAccepted = 480
    segmentationSupported = segmentedBoth
    vendorID = 8


There are a few different forms of the *whois* command supported by this 
simple application.  You can see these with the help command::

    > help whois
    whois [ <addr>] [ <lolimit> <hilimit> ]

This is like a BNF syntax, the **whois** command is optionally 
followed by a BACnet device address, and then optionally followed by a
low (address) limit and high (address) limit.  The most common use of the Who-Is
request is to look for a specific device given its device
identifier::

    > whois 1000 1000

If the site has a numbering scheme for groups of BACnet devices (i.e. grouped
by building), then it is common to look for all the devices in a specific
building as a group::

    > whois 203000 203099

Every once in a while a contractor might install a BACnet 
device that hasn't been properly configured.  Assuming that
it has an IP address, you can send an **unconstrained Who-Is** request 
to the specific device and hope that it responds::

    > whois 192.168.0.10

    > pduSource = <Address 192.168.0.10>
    iAmDeviceIdentifier = ('device', 1000)
    maxAPDULengthAccepted = 1024
    segmentationSupported = segmentedBoth
    vendorID = 15

There are other forms of BACnet addresses used in BACpypes,
but that is a subject of an other tutorial.


What's Next
-----------

The next tutorial describes the different ways this 
application can be run, and what the commands can tell you
about how it is working.  All of the "console" applications  
(i.e. those that prompt for commands) use the same basic 
commands and work the same way.

