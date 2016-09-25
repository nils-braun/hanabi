# Some general utility functions used throughout the project.
import os
import sys
from functools import wraps
from urllib.parse import urlparse, urljoin

from flask import session, g, flash, redirect, url_for, request, render_template


def set_basic_configuration_and_views(app):
    """
    Set the configurations and functionality specific to this project:
        1. Add a proper error page
        2. Add the user functionality and views
        3. Add the game functionality and views
        4. Set the start page to be game/home

    :param app: Which app to configure
    """
    if not app.config['DEBUG']:
        install_secret_key(app)

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    from app.users.views import mod as users_module
    app.register_blueprint(users_module)

    from app.game.views import mod as game_module
    app.register_blueprint(game_module)

    @app.route("/")
    def index():
        return redirect(url_for("game.home"))


def add_before_request(mod):
    """
    Function to pull the current user's profile from the database before the request is treated.
    It is added as a before_request function to the given blueprint module.
    """
    def before_request():
        g.user = None
        if 'user_id' in session:
            # Do only import the User here, otherwise we will end up with cyclic dependencies.
            from app.users.models import User
            g.user = User.query.get(session['user_id'])

    mod.before_request(before_request)


def requires_login(f):
    """
    Function decorator to require a logged in user before accessing a wrapped flask route.
    Use it with

        @mod.route("/page/")
        @requires_login
        def route_for_page():
            ...

    to make /page/ only accessible for logged in users.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash(u'You need to be signed in for this page.')
            return redirect(url_for('users.login', next=request.path))
        return f(*args, **kwargs)

    return decorated_function


def render_template_with_user(template_path, **kwargs):
    """
    Helper function to render the template behind the given template path, and replace the following
    variables in this template:

        1. If a user is logged in, {{ user }} is replaced by the current user.
        2. If a download ID is set, download_id is set to is, otherwise to None.
        3. Everything else given in the remaining keyword arguments.

    Use it analogous to the render_template function by Flask:

        @mod.route("/page/")
        def route():
            return render_template_with_user("template.html", variable=1, some_stuff="others")

    :param template_path: Which template to render.
    :param kwargs: Which other variables to replace in the template apart from the user and the download ID.
    :return: the rendered template.
    """
    if g.user:
        return render_template(template_path, user=g.user, **kwargs)
    else:
        return render_template(template_path, **kwargs)


def is_safe_url(target):
    """
    TODO: Copy from where?
    :param target:
    :return:
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target():
    """
    TODO: Copy from where?
    :return:
    """
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


def redirect_back_or(endpoint, **values):
    """
    TODO: Copy from where?
    :param endpoint:
    :param values:
    :return:
    """
    target = request.form.get('next')
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


def install_secret_key(app, filename='secret_key'):
    """
    TODO: Copy from where?
    Configure the SECRET_KEY from a file
    in the instance directory.

    If the file does not exist, print instructions
    to create it from a shell with a random key,
    then exit.
    """
    filename = os.path.join(app.instance_path, filename)

    try:
        app.config['SECRET_KEY'] = open(filename, 'rb').read()
    except IOError:
        print('Error: No secret key. Create it with:')
        full_path = os.path.dirname(filename)
        if not os.path.isdir(full_path):
            print('mkdir -p {filename}'.format(filename=full_path))
        print('head -c 24 /dev/urandom > {filename}'.format(filename=filename))
        sys.exit(1)
