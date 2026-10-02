import http.server, socketserver, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def do_GET(self):
        # Same rule as _redirects: /projets/* -> /index.html (200)
        if self.path.split('?')[0].startswith('/projets/'):
            self.path = '/index.html'
        return super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(('', PORT), Handler) as httpd:
    httpd.serve_forever()
