import flask
import jinja2

import webapp.docs
import webapp.views


flask_app = flask.Flask(__name__)


flask_app.register_blueprint(webapp.docs.blueprint)
flask_app.register_blueprint(webapp.views.blueprint)


if __name__ == '__main__':
    flask_app.run(debug=True)
