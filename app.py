import os
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from models import db, User

# ------------------------------------------------------------------
# Flask + extensions
# ------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_in_production'

# ---- Database path (absolute, works on Windows) ----
basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, 'instance')
os.makedirs(instance_dir, exist_ok=True)          # create folder if missing
db_path = os.path.join(instance_dir, 'church.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'          # route name for login page
socketio = SocketIO(app)

# ------------------------------------------------------------------
# User loader
# ------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------------------------------------------------
# Register blueprints / routes
# ------------------------------------------------------------------
from routes import *   # <-- this imports all @app.route definitions

# ------------------------------------------------------------------
# Create tables + default admin
# ------------------------------------------------------------------
with app.app_context():
    db.create_all()
    if not User.query.first():
        admin = User(username='admin')
        admin.set_password('password')      # <-- change later!
        db.session.add(admin)
        db.session.commit()

# ------------------------------------------------------------------
# Run
# ------------------------------------------------------------------
if __name__ == '__main__':
    socketio.run(app, debug=True)