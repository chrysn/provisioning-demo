#!/usr/bin/env python3
"""A very primitive CA relay that does three things:

* It runs an HTTP server, receiving POSTs of CSRs to /sign and returns
  certificates (or certificate chains).
* Before accepting the CSR, it checks whether the claimed name(s) correspond to
  the expressed key (in what is currently a custom scheme that should evolve
  into something standardizable).
  (This step is not implemmented yet).
* To sign the certificates, it calls out to a preconfigured acme.sh command.

This tool is very much not suited for production (being single-threaded and
calling out to programs of which the author did not check whether they're good
to use with untrusted input.

This program takes no arguments; all configuration is hard-coded.
"""

import sys
from http import server
import tempfile
import subprocess

command = lambda csrname, certname: ['../acme.sh/acme.sh', '--test', '--dns', 'dns_mine', '--signcsr', '--dnssleep', '2', '--csr', csrname, '--cert-file', certname]

class Handler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        msg = '''Bad request: Only POST to /sign, and put CSRs in there\n\n----\n\n''' + __doc__
        self.send_response(400)
        self.end_headers()
        self.wfile.write(msg.encode('utf8'))

    def do_POST(self):
        import sys
        l = int(self.headers['Content-Length'])
        if l > 2048:
            raise ValueError
        with tempfile.TemporaryDirectory(prefix="relay-ca") as td:
            csr = self.rfile.read(l)
            csrname = td + "/request.csr"
            certname = td + "/certificate.pem"
            with open(csrname, 'wb') as f:
                f.write(csr)
            subprocess.check_call(command(csrname, certname))
            cert = open(certname, 'rb').read()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(cert)

def run():
    if len(sys.argv) != 1:
        print(__doc__)
        sys.exit(1)
    server_address = ('', 9885)
    httpd = server.HTTPServer(server_address, Handler)
    httpd.serve_forever()

if __name__ == "__main__":
    run()
