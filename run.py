from flask import Flask, render_template, request, jsonify
from app import create_app

app = create_app()

@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')  # 🔹 Admin paneli rotası

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
