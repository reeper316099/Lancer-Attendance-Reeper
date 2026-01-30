import os
from flask import Flask
from .views import views


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
    app.register_blueprint(views, url_prefix="/")

    return app
