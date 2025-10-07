import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from api.index import app

def handler(event, context):
    from werkzeug.wrappers import Request, Response
    from werkzeug.serving import WSGIRequestHandler
    import io
    
    # Convert Netlify event to WSGI environ
    environ = {
        'REQUEST_METHOD': event.get('httpMethod', 'GET'),
        'PATH_INFO': event.get('path', '/'),
        'QUERY_STRING': event.get('queryStringParameters', ''),
        'CONTENT_TYPE': event.get('headers', {}).get('content-type', ''),
        'CONTENT_LENGTH': str(len(event.get('body', ''))),
        'wsgi.input': io.StringIO(event.get('body', '')),
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
        'wsgi.url_scheme': 'https',
        'SERVER_NAME': event.get('headers', {}).get('host', 'localhost'),
        'SERVER_PORT': '443',
    }
    
    # Add headers to environ
    for key, value in event.get('headers', {}).items():
        key = 'HTTP_' + key.upper().replace('-', '_')
        environ[key] = value
    
    response_data = []
    
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    # Call the Flask app
    app_response = app(environ, start_response)
    
    # Convert response
    body = b''.join(app_response).decode('utf-8')
    
    return {
        'statusCode': int(response_data[0].split()[0]),
        'headers': dict(response_data[1]),
        'body': body
    }
