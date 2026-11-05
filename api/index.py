import sys
import os
from urllib.parse import parse_qs, urlencode

# Ensure project root directory is on the Python module search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

class VercelWSGIMiddleware:
    """
    WSGI middleware for Vercel Serverless Python:
    Extracts the original routed path forwarded via __path__ or headers,
    normalizing PATH_INFO so all routes match correctly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get('QUERY_STRING', '')
        if '__path__' in qs:
            params = parse_qs(qs, keep_blank_values=True)
            if '__path__' in params:
                raw_path = params.pop('__path__')[0]
                target_path = '/' + raw_path.lstrip('/')
                environ['PATH_INFO'] = target_path
                environ['QUERY_STRING'] = urlencode(params, doseq=True)
        else:
            path = environ.get('PATH_INFO', '')
            matched_path = environ.get('HTTP_X_MATCHED_PATH')
            if matched_path and not matched_path.startswith('/api/index.py'):
                environ['PATH_INFO'] = matched_path
            elif path == '/api/index.py' or path == '/api/index.py/':
                environ['PATH_INFO'] = '/'
            elif path.startswith('/api/index.py/'):
                environ['PATH_INFO'] = path[len('/api/index.py'):]
            elif path.startswith('/api/'):
                environ['PATH_INFO'] = path[len('/api'):]

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
