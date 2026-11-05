import sys
import os

# Ensure project root directory is on the Python module search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

class VercelWSGIMiddleware:
    """
    Middleware for Vercel Serverless Python:
    Vercel rewrites can prepend '/api/index.py' to PATH_INFO.
    This middleware normalizes PATH_INFO to match standard Flask routes.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        # Check if Vercel forwarded original path in headers
        matched_path = environ.get('HTTP_X_MATCHED_PATH')
        if matched_path and not matched_path.startswith('/api/index.py'):
            environ['PATH_INFO'] = matched_path
        elif path.startswith('/api/index.py'):
            cleaned = path[len('/api/index.py'):]
            environ['PATH_INFO'] = cleaned if cleaned.startswith('/') else ('/' + cleaned)
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
