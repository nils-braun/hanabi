# Main entry point for the web service. Here we will create a new "app" instance,
# which is the Flask web service, and add all the needed configuration options
# for this project.
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

#from app.functions import set_basic_configuration_and_views

# Create a new Flask application
app = Flask(__name__)

# Load some configuration options from the file config.py
app.config.from_object('config')

# Create a new database connection, we will use everywhere, using the settings in this application
db = SQLAlchemy(app, session_options={"autoflush": False})

# Add the configurations and functionality specific to this web service.
#set_basic_configuration_and_views(app)