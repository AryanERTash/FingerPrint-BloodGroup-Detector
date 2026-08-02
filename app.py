import os
from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Hello from Flask on Render!"
    })

@app.route('/about')
def about():
    return jsonify({
        "status": "success",
        "message": "Flask API is running smoothly from the root directory."
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)