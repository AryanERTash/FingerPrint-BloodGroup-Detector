import os
from flask import Flask, render_template, request, jsonify

# Calculate root path relative to the api directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(
    __name__,
    template_folder=os.path.join(base_dir, 'templates'),
    static_folder=os.path.join(base_dir, 'static')
)

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Hello from Flask on Vercel!"
    })

@app.route('/about')
def about():
    return jsonify({
        "status": "success",
        "message": "Flask API is running smoothly."
    })

# Catches all undefined routes and returns JSON response
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({
        "status": "error",
        "message": "Route not found"
    }), 404

# For local development only
if __name__ == '__main__':
    app.run(debug=True)