import flask
import jinja2

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import webapp.docs
import webapp.views
from webapp.models import flask_app


# flask_app = flask.Flask(__name__)


flask_app.register_blueprint(webapp.docs.blueprint)
flask_app.register_blueprint(webapp.views.blueprint)


if __name__ == '__main__':
    flask_app.run(debug=True)
