HTTPS certificate demo for home routers
=======================================

This is a playground for practical experimentation around homerouter-provisioning__.

.. __: https://datatracker.ietf.org/doc/draft-richardson-homerouter-provisioning/

The path currently being explored is aiming at getting ACME certificates (from `Let's Encrypt`__)
onto devices that may not even have a route to the public Internet,
all while retaining the properties of HTTPS.
This is taking ideas from rdlink_, without being strictly dependent on it in this stage.

.. __: https://letsencrypt.org/
.. _rdlink: https://datatracker.ietf.org/doc/draft-amsuess-t2trg-rdlink/

(A way forward is envisioned that'd allow for fully local operation,
and that will require a specification like rdlink).

User story
----------

(This is not presently provided by the tools in here, but is what should eventually be demonstrated).

Provisioning a non-routing device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A home entertainment system is unboxed, and gets wired into the local network.
Following the setup manual, the user scans the QR code on the device's display from their browser's address bar,
sees a green lock with the vendor's name on it,
and configures how they want to authenticate to the device in the future.

Behind the scenes,
the enternainment system tried to obtain time and a valid certificate over the network.
The user is running a strict firewall that doesn't allow new devices to access the Internet, so that step failed.
The device got an address (2001:db8::c0ff:ee), though, and thus presented the following address on its QR code::

    http://400gre0000000000000c1vo0to.at.zyk3rwfhkecc3lvb5ajweedxvpfredfqna5xycacamy4zltddvaq.devices.example.com

When first accessed, the browser mediates a certificate exchange with the server running devices.example.com,
and provides the home entertainment system with a valid certificate for
``*.at.zyk3rwfhkecc3lvb5ajweedxvpfredfqna5xycacamy4zltddvaq.devices.example.com``.
Once that is installed (a few seconds after the user scanned the code),
the user is redirected to::

    https://400gre0000000000000c1vo0to.at.zyk3rwfhkecc3lvb5ajweedxvpfredfqna5xycacamy4zltddvaq.devices.example.com

which shows the nice welcoming green lock.

Provisoning a router
~~~~~~~~~~~~~~~~~~~~

A cellular modem and WiFi router is unboxed and initially powered up;
no SIM card is provided because eSIM credentials will be entered later on.
The setup manual asks the user to join the router's default WiFi using a WPS button,
and to scan the QR code provided in the manual into the browser.

The user is presented with an *insecure* URI,
but all that happens there is that the user is asked to connect back to a different existing network and keep the tab open.
A few seconds after that network connection is established,
the web site display instructs the user to connect back to the router's network,
where it switches over to a friendly lock with the vendor's name in the address bar,
and proceeds to installation.

Behind the scenes,
the router picked a ULA address based on its serial number,
and that ULA as well as the router's public key hash were dynamically printed into its leaflet
(like a serial number would be).
The loaded web site was primed with a certificate signing request from the router;
once Internet connectivity was available again,
it opened up a connection as in the home entertainment case
and kept the certificate in the browser until it could be passed back to the router after the second network change.

State and further extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~

All the steps describe above should, in the author's opinion, be possible with current web browsers or similar devices.

Several enhancements are conceivable but hinge on changes to web browsers or other experimental techniques:

* If browsers can be made to accept certificates based on hyperlocal DANE-like promises
  (domains like devices.example.com stating that "for any X.devices.example.com, ``_443._tcp.X.devices.example.com TLSA 3 1 1 X`` is a valid record"),
  then these steps can be performed fully offline.

* If it can be assumed that a device can announce a ULA in about any network
  (as is suggested by `recent homenet activity`__),
  then the home entertainment system can pick one based on its identity
  and have a QR code provided in its box rather than needing to display one.

  (The alternative here would be using link-local addresses,
  but these may be troublesome to get around through DNS).

.. __: https://datatracker.ietf.org/doc/draft-lemon-stub-networks/

An enhancement that should be possible without any such caveats is vendor independence:
in both examples, the devices could have a list of domains to ask certficiates from,
or even let the network provide one by means similar to DNS service discovery.
This allows robustness against vendor services shutting down,
and would (on tightly administered sites) even allow operation separate from the Internet,
provided a locally recognized certification authority provides the certificates.

Under various conditions,
steps can be taken by the device to shorten the entry URI;
however, as these conditions may not be met,
the long versions will be needed for fallback anyway.
(In particular, the RPK expressed in the thrid component can be shortened to a serial number if it is known that the vendor will sign the CSR,
but that loses vendor independence;
likewise, hard-coding a shorter name to a known ULA address requires knowledge of that mapping and in addition the feasibility of the own-ULA extension).

Implemented components
----------------------

Of all this, a few small parts are implemented in components in this repository:

* ...
