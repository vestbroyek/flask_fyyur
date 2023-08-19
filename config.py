from flask import Flask
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import os

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
# Docker database URI
# run with: docker run -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fyyur --rm postgres
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/fyyur"

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
app.config["DEBUG"] = True
app.config["FLASK_ENV"] = "development"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config['WTF_CSRF_ENABLED'] = False

db = SQLAlchemy(app)
