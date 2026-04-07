from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import time

# 1. Initialize App and Database FIRST
app = Flask(__name__)
app.secret_key = 'super_secret_safety_key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'women_safety.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 2. Global Cooldown Variable
last_alert_time = 0 

# 3. Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    emergency_contact = db.Column(db.String(20), nullable=False)

# 4. Routes
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
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
            print(f"✅ LOGIN SUCCESS: Welcome {u_name}")
            return redirect(url_for('home'))
        return "Login Failed. <a href='/login'>Try again</a>"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u_name = request.form['username'].strip()
        existing_user = User.query.filter_by(username=u_name).first()
        if existing_user:
            return "User already exists! <a href='/login'>Login here</a>"
        
        new_user = User(
            username=u_name, 
            password=request.form['password'].strip(), 
            emergency_contact=request.form['contact'].strip()
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/alert', methods=['POST'])
def handle_alert():
    global last_alert_time
    current_time = time.time()
    
    # 10 second cooldown to prevent terminal spamming
    if current_time - last_alert_time < 10:
        return jsonify({"status": "Cooldown active"}), 200

    if 'user_id' in session:
        data = request.json
        user = db.session.get(User, session['user_id']) # Updated for SQLAlchemy 2.0
        last_alert_time = current_time

        print("\n" + "🚨" * 20)
        print(f"!!! SOS EMERGENCY ALERT !!!")
        print(f"USER: {user.username}")
        print(f"EMERGENCY CONTACT: {user.emergency_contact}")
        # FIXED MAPS LINK
        print(f"LOCATION: https://google.com{data['lat']},{data['lng']}")
        print("🚨" * 20 + "\n")
        
        return jsonify({"status": "Alert Sent Successfully!"})
    return jsonify({"status": "Unauthorized"}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=False)
