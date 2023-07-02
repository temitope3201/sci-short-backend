from flask import Flask
from flask_restx import Api
from .config import config_dict
from .utils import db
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from api.models import User, Url, Clicks
from .users.views import user_namespace
from flask_mail import Mail
from .urls.views import urls_namespace
import os
from .main.views import main_namespace
from flask_cors import CORS
from .utils import cache, limiter







mail = Mail()

def create_app(config = config_dict['prod']):

    app = Flask(__name__)

    authorizations ={
        "Bearer Auth":{
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description":"Add a JWT token to the Header with **Bearer&lt;JWT&gt token to authorize"
        }
    }

    api = Api(app,
              title="SCI-SHORT URL Shortener API", 
              description="This is a URL Shortener API build with Flask RESTX in Python.",
              version=1.0,
              authorizations= authorizations,
              security="Bearer Auth")

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 465
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USER")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASS")
    app.config["MAIL_USE_TLS"] = False
    app.config["MAIL_USE_SSL"] = True

    global cache
    global limiter

    app.config.from_object(config)
    db.init_app(app)
    limiter.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache'})

    CORS(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    mail = Mail(app)
    


    api.add_namespace(user_namespace, path ='/users')
    api.add_namespace(urls_namespace, path='/urls')
    api.add_namespace(main_namespace, path='')

    @app.shell_context_processor
    def make_shell_context():

        return{
            'db': db,
            'user': User,
            'url': Url,
            'clicks': Clicks
        }


    return app


    