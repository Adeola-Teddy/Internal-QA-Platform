from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
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
#DATABASE CONNECTION
if not os.path.exists(os.path.join(basedir, 'mydatabase.sqlite')):
    conn = sqlite3.connect(os.path.join(basedir, 'mydatabase.sqlite'))
    conn.close()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'mydatabase.sqlite')
db = SQLAlchemy(app)
# USER DATABASE #
class UsersDB(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique = True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username
# QUESTIONS DATABASE #
class QuestionDB(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body = db.Column(db.String(20), nullable=False)
    upvotes = db.Column(db.Integer)

    author = db.relationship('UsersDB', backref=db.backref('questions', lazy=True))
#CREATES THE DATABASE
with app.app_context():
    db.create_all()

# USER FOR THE FORMS AND FLASK_LOGIN #
# Define user model
class User(UserMixin):
    def __init__(self, id):
        self.id = id
    
    def __repr__(self):
        return f"<User {self.id}>"

#CONNECTS THE DATABSE TO WEBPAGE/FORMS
engine = create_engine('sqlite:///' + os.path.join(basedir, 'mydatabase.sqlite'))
Session = sessionmaker(bind=engine)
session = Session()
#INBUILT FLASK_LOGIN
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
#LOGIN REST API
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

#LOGOUT OF WEBSITE (STILL IN PROTECTED PAGE)
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#FOR THE SIGNUP REST API
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
        else:
            return(render_template('signup.html', form=form, error='Username already taken.'))
    return(render_template('signup.html', form=form, error = ""))

#PROTECTED PAGE (Q&A PAGE)
class QuestionForm(FlaskForm):
    question = StringField('question')
    submit = SubmitField('Submit')

@app.route('/protected', methods=['GET', 'POST'])
@login_required
def protected():
    s = str(current_user)
    username1 = s.replace('<User ', '').replace('>', '')

    question_form = QuestionForm()
    if request.method == 'POST':
        if question_form.validate_on_submit():
            user = UsersDB.query.filter_by(username=username1).first()
            new_question = QuestionDB(author=user, body=question_form.question.data, upvotes=0)
            db.session.add(new_question)
            db.session.commit()

    return render_template('protected.html', user_logged=username1,  form1=question_form)