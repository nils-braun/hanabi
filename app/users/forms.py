from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Email


class LoginForm(Form):
    """
    Form to login with an already registered user.
    """
    email = StringField('Email address', [DataRequired(), Email()])
    password = PasswordField('Password', [DataRequired()])


class RegisterForm(Form):
    """
    Form to create a new user.
    """
    name = StringField('Name', [DataRequired()])
    email = StringField('Email address', [DataRequired(), Email()])
    password = PasswordField('Password', [DataRequired()])
    confirm = PasswordField('Repeat Password', [DataRequired(), EqualTo('password', message='Passwords must match')])
