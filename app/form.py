from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email = StringField('email', validators = [DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class RegisterForm(FlaskForm):
    email = StringField('email', validators = [DataRequired(), Email()])
    nickname = StringField('nickname', validators=[DataRequired()])

class EditForm(FlaskForm):
    nickname = StringField('nickname', validators=[DataRequired()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('old_password', validators=[DataRequired()])
    new_password = PasswordField('new_password', validators=[DataRequired()])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired()])

class PostForm(FlaskForm):
    post = StringField('post', validators=[DataRequired()])

class SearchForm(FlaskForm):
    search = StringField('search', validators=[DataRequired()])




