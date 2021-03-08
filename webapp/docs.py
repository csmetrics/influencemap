import flask

blueprint = flask.Blueprint('docs', __name__,
                            template_folder='templates/vast')


@blueprint.route('/vast19')
def vast19():
    return render_template("vast19.html")
