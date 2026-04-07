from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import time

app = Flask(__name__)
app.secret_key = 'super_secret_safety_key'

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'women_safety.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODEL ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    emergency_contact = db.Column(db.String(20), nullable=False)

# --- THE FIX: THIS CREATES THE DATABASE ON RENDER ---
with app.app_context():
    db.create_all()

last_alert_time = 0 

# --- ROUTES ---
@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', user=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u_name = request.form['username'].strip()
        u_pass = request.form['password'].strip()
        user = User.query.filter_by(username=u_name).first()
        if user and user.password == u_pass:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        return "Invalid credentials. <a href='/login'>Try again</a>"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u_name = request.form['username'].strip()
        new_user = User(username=u_name, password=request.form['password'].strip(), emergency_contact=request.form['contact'].strip())
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/alert', methods=['POST'])
def handle_alert():
    global last_alert_time
    current_time = time.time()
    if current_time - last_alert_time < 10:
        return jsonify({"status": "Cooldown"}), 200
    
    if 'user_id' in session:
        data = request.json
        user = db.session.get(User, session['user_id'])
        last_alert_time = current_time
        print(f"\n🚨 SOS! USER: {user.username} | LOC: {data['lat']},{data['lng']}\n")
        return jsonify({"status": "Success"})
    return jsonify({"status": "Unauthorized"}), 401

if __name__ == '__main__':
    app.run(debug=False)
