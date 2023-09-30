from flask import Flask, send_from_directory, request, make_response

app = Flask(__name__)

@app.route('/')
def serve_index():
   return send_from_directory('public', 'index.html')

@app.route('/public/<path:resource>')
def serve_file(resource):
    return send_from_directory('public', resource)


@app.after_request
def apply_nosniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

