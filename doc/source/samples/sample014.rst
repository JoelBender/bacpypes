.. BACpypes sample code 14

Sample 14 - Getting External Data
=================================

This is a pair of sample applications: a server that provides key:value updates
in the form of JSON objects; and a client that periodically polls the server
for updates and applies them to a cache.

Server Code
-----------

The server is based on SimpleHTTPServer examples, the only interesting part of
the code is responding to a GET request::

    class ValueServer(SimpleHTTPServer.SimpleHTTPRequestHandler):
    
        def do_GET(self):
            cache_update = {choice(varNames): uniform(0, 100)}
            simplejson.dump(cache_update, self.wfile)

The cache update is a key name, selected randomly from the *varNames* list, and
a value between 0 and 100.  This is such a simple example that *str()* and 
*eval()* could just as easily been used.

Client Code
-----------

This is a long line of text.
