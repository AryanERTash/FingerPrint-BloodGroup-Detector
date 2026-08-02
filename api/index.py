from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route('/')
def home():
    return jsonify({"message": "Hello from Flask on Vercel!"})

@app.route('/about')
def about():
    return jsonify({"status": "Flask API is running smoothly."})

if __name__ == '__main__':
    app.run(debug=True)