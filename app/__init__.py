from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from os import path

app = Flask(__name__)

if 'home/web/' in path.abspath(__file__):
    app.config.from_object('config.ProductionConfig')
else:
    app.config.from_object('config.DevelopmentConfig')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице'

from app import views
login_manager.login_view = 'signup'
