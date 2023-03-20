from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import os
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your-secret-key'
app.config['STATIC_FOLDER'] = 'static'
# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)

basedir = os.path.abspath(os.path.dirname(__file__))

if not os.path.exists(os.path.join(basedir, 'mydatabase.sqlite')):
    conn = sqlite3.connect(os.path.join(basedir, 'mydatabase.sqlite'))
    conn.close()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'mydatabase.sqlite')
db = SQLAlchemy(app)

class UsersDB(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique = True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

with app.app_context():
    db.create_all()


# Define user model
class User(UserMixin):
    def __init__(self, id):
        self.id = id
    
    def __repr__(self):
        return f"<User {self.id}>"

# Define some users

users = {'foo': {'password': 'bar'}, 'baz': {'password': 'qux'}}

engine = create_engine('sqlite:///' + os.path.join(basedir, 'mydatabase.sqlite'))
Session = sessionmaker(bind=engine)
session = Session()

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username1 = request.form['username']
        password2 = request.form['password']
        results = session.query(UsersDB).filter_by(username=username1, password=password2).all()
        if results:
            user = User(username1)
            login_user(user)
            return redirect(url_for('protected'))
        else:
            return render_template('login.html', error='Invalid username or password')
    else:
        return render_template('login.html')

@app.route('/protected')
@login_required
def protected():
    return render_template('protected.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

class MyForm(FlaskForm):
    username = StringField('username')
    password = StringField('password')
    submit = SubmitField('Submit')

@app.route('/signup', methods=['GET', 'POST'])
def index():
    form = MyForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # code to handle form data
        if not session.query(UsersDB).filter_by(username=username).all():
            new_user = UsersDB(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return(render_template('login.html', error='Thank you for registering! Please login!'))
    return(render_template('signup.html', form=form, error='Username already taken.'))
