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

    http://at-400gre0000000000000c1vo0to.zyk3rwfhkecc3lvb5ajweedxvpfredfqna5xycacamy4zltddvaq.devices.example.com

When first accessed, the browser mediates a certificate exchange with the server running devices.example.com,
and provides the home entertainment system with a valid certificate for
``*.zyk3rwfhkecc3lvb5ajweedxvpfredfqna5xycacamy4zltddvaq.devices.example.com``.
Once that is installed (a few seconds after the user scanned the code),
the user is redirected to::

    https://at-400gre0000000000000c1vo0to.zyk3rwfhkecc3lvb5ajweedxvpfredfqna5xycacamy4zltddvaq.devices.example.com

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

Other extensions are possible without these caveats,
but are just left as an exercise to the reader to allow this to stay focused:

* Vendor independence:
  in both examples, the devices could have a list of domains to ask certficiates from,
  or even let the network provide one by means similar to DNS service discovery.
  This allows robustness against vendor services shutting down,
  and would (on tightly administered sites) even allow operation separate from the Internet,
  provided a locally recognized certification authority provides the certificates.

* Vendor signing:
  A vendor can limit signing on its own domain to devices that additionally prove to run the vendor's firmware,
  be that by means of remote attestation
  or by prior knowledge of device public keys.

  They can then use the claims encoded by a device having a cetificate for `https://something.device.vendor.com`
  to ease further onboarding.

* All demos are currently aiming at IPv4.
  Serving A records for equivalent shorter-prefixed names should be trivial.
  That old IP version wouldn't allow any ULA tricks.
  In the router setup case, the router would instead pick private addresses
  (and could do so reliably enough to print them);
  the simplification to announce a ULA and thus allow static links in the non-router case would become inapplicable.

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

* ./implementation/dns-server/:
  A DNS server based on updns_ (written in Rust) that

  * serves `at-(base32-of-address).* IN AAAA address` records

  * answers any request to `_acme-challenge.*` from a file /tmp/token populated by the next component

* ./implementation/acme.sh/dnsapi/dns_mine.sh:
  An acme.sh_ API add-on that writes to /tmp/token.

* ./implementation/acme-relay/relay.py:
  A web service to run acme.sh;
  this is a primitive version of what the vendor should have running.
  It offers a very simple "POST your CSR and receive a certificate" API.
  (In a somewhat more standardization-oriented scenario,
  this may be exactly the ACME API,
  just that for the CSRs we're dealing with, many of the checking steps are different).

.. _updns: https://github.com/wyhaya/updns
.. _acme.sh: https://github.com/acmesh-official/acme.sh

Usage
~~~~~

* Set up some domain such that your development host can serve as a public DNS server.

  I found this easiiest to do by doing a full delegation like this at amsuess.com::

      alt.prometheus                  IN      AAAA    2a01:4f8:190:3064::3
      devices-test                    IN      NS      alt.prometheus.amsuess.com.

  but that ultimately depends on your DNS setup.

  Note that NS records always "point to port 53", so you'll
  a) need an IP address to which no DNS server is bound yet, and
  b) need to run the later DNS server on a privileged port.

  There are all kinds of setups to make this more production-ready --
  but taking a new IP address and running ``sudo`` is what works best for me.

* Run updns::

      $ cd implementation/dns-server
      $ cat >config <<EOF
      bind [2a01:4f8:190:3064::3]:53
      proxy 0.0.0.0:53
      EOF
      $ cargo build
      $ sudo target/debug/updns -c ./config

  The necessary ``cargo`` tool can come from any Rust installation.

  The proxy line is a crude way to disable request forwarding,
  which is a feature of updns unused here
  (and disabling it this way ensures that failing requests are answered quickly).

* Obtain certificates using acme.sh_.

  Get a copy of acme.sh (for the next steps, ideally into ./implementation/),
  and symlink ./implementation/acme.sh-addons/dnsapi/dns_mine.sh into its dnsapi directory.

  To try it out, you can run acme.sh right here::

      ./acme.sh --test --issue --dns dns_mine -d '*.hash-of-my-public-key.devices-test.amsuess.com'

  If DNS forwarding is set up correctly, this should eventually show a certificate
  (for a key it generated on its own at this stage).

* Locally on a to-be-certified device, generate a key and CSR::

      # i'd prefer just using `openssl genpkey -algorithm ed25519`, but
      # acme.sh's _readKeyLengthFromCSR doesn't work on those
      openssl ecparam -genkey -name secp256r1 | openssl ec -out my.key
      # -subj could just as well be "/", which works with acme-tiny (which
      # can't do DNS) but is rejected by acme.sh. Using literally the same CN
      # as the SAN (even though it probably doesn't work like that for a CN)
      # ensures that there is just one TXT record to be added (which is all the
      # updns fork can do).
      openssl ecparam -genkey -name secp384r1 | openssl ec -out my.key
      openssl req -new -key my.key -subj "/CN=*.hash-of-my-public-key.devices-test.amsuess.com" -reqexts SAN -config <(cat /etc/ssl/openssl.cnf <(printf "[SAN]\nsubjectAltName=DNS:*.hash-of-my-public-key.devices-test.amsuess.com")) > my.csr

  So far, this literally says "hash-of-my-public-key" where there should be a hash --
  but right now that's OK because relay.py doesn't check yet.

  Again, this can be tested with acme.sh

* Inside implementation/acme-relay, run ``./relay.py``.

  This opens a web server at port 9885, through which you can get certificates for your CSRs generated before::

      curl --data-binary @./my.csr http://localhost:9885/

  If the ``--test`` flag is stripped out of the relay script,
  the resulting certificates can be used to get local HTTPS running:

  .. image:: screenshots/20210529-green-locally.png
     :alt: Screenshot of an unmodified Firefox browser at <https://at-vmf3rvbb9g011smoi9o8u8gees.hash-of-my-public-key.devices-test.amsuess.com:8001/>, showing a "You are securely connected to this site" / "Verified by: Let's Encryt".

Next steps
~~~~~~~~~~

* Decide on a public-key-to-hostname scheme, and check that in relay.py.

* Let that web server verify if the underlying key matches the hash of the public key.
  After all, while we *may* let the ACME authority sign anything under our domain control, we don't *want* to.

  (At this step, it may also check whether the rest of the host name matches --
  not that Let's Encrypt would sign us such certificates, but why bother them.)

* Write a short web site (to be served by the device) that sends such a request.

  Serving that site will need at least some form of CSR as input,
  probably the hash-of-my-public-key (to avoid doing any certificate handling in JavaScript),
  and a way to post the result back to the server.

* Write a server that creates a key,
  finds its best usable address,
  joins those into an single link,
  serves the script on that link,
  and takes up HTTPS as soon as it receives a certificate.

  (For the router use case, no extra DNS server is needed;
  the existing updns-based one can be announced as a (low-priority, if that's a thing) DNS server by the unconnected router
  and gives all the resolution the client needs until it reaches the full Internet.)

Future evolution
----------------

To get this all to work even fully offline,
a domain will need to make a promise to always issue ``(base32-of-address).at.*.(domain) IN A(AAA) address`` records,
and that anyone prooving possession of the encoded key is eligible for certificates for ``(encoded-key).(domain)``
(essentially, producing ``(encoded-key).(domain) IN TLSA 3 1 0 (key)`` statements).

As domains are issued in a time limited fashion,
it may make sense to establish such a domain under IETF / IANA control under the ``.arpa`` subdomain.

Until browsers recognize such a domain,
browser recognition can locally be emulated to obtain the desired behavior before browser support is present by two means:

* A local resolver component is provided that provides the A(AAA) records for any address under the known domain.

  When compatibility with the service provided by global DNS is not necessary,
  that service may also resolve names without the ``at-(base32)`` part as outlined in rdlink_.

* A locally run CA service can replace the web server,
  using a mechanism similar to the vendor fallback.
  (With a little handwaving, one could say that devices should always fall back to taking certificates from ``https://certificate-authority.local//`` if that name can be resolved).

  The local service (which would typically be run at the host's loopback interface)
  would issue certificates for the known domain provided the proof of possesion checks out,
  and be installed as a local CA in the browser.

  Some additional measures may be necessary to ensure that this kind of certificate will not get used
  to authenticate the device towards different clients.
