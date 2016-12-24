from flask.ext.wtf import Form
from wtforms import PasswordField, BooleanField, RadioField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, Optional, Length, Email


class SignUpForm(Form):
    email = EmailField('Email', [InputRequired('Пожалуйста, введите Email'),
                                 Email('Введенный Email не существует.')])


class LoginForm(Form):
    password = PasswordField('Код из email', [
        InputRequired('Пожалуйста, введите код'),
    ])
    remember_me = BooleanField('Запомнить меня', default=False)


class ReviewForm(Form):
    rating = RadioField('Ваша оценка:', [InputRequired('Пожалуйста, выберете вашу оценку')],
                        choices=[('good', '<span class="text-success">хорошо</span>'),
                                 ('bad', '<span class="text-danger">плохо</span>')])
    review = TextAreaField('Ваш отзыв', [Optional(),
                                         Length(max=200, message='Отзыв не может быть длиннее 200 символов')])
