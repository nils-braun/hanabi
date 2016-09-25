from app import db
from app.functions import render_template_with_user, requires_login, add_before_request, redirect_back_or, \
    get_redirect_target
from app.users.forms import RegisterForm, LoginForm
from app.users.models import User
from flask import Blueprint, request, flash, g, session, redirect, url_for
from werkzeug import check_password_hash, generate_password_hash

mod = Blueprint('users', __name__, url_prefix='/users')
add_before_request(mod)


@mod.route('/logout/', methods=['GET', 'POST'])
def logout():
    if g.user:
        del g.user

        if "user_id" in session:
            del session["user_id"]

        if "download_id" in session:
            del session["download_id"]

        flash("Successfully logged out.")

    return redirect(url_for("users.login"))


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Login form
    """
    if g.user:
        flash("You are already logged in!")
        return redirect_back_or("game.home")

    form = LoginForm(request.form)
    next_url = get_redirect_target()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # we use werzeug to validate user's password
        if user and check_password_hash(user.password, form.password.data):
            # the session can't be modified as it's signed,
            # it's a safe place to store the user id
            session['user_id'] = user.id
            flash('Welcome %s' % user.name)
            return redirect_back_or('game.home')

        flash('Wrong email or password', 'error-message')
    return render_template_with_user("users/login.html", form=form, next=next_url)


@mod.route('/register/', methods=['GET', 'POST'])
@requires_login
def register():
    """
    Registration Form
    """
    form = RegisterForm(request.form)
    next_url = get_redirect_target()

    if form.validate_on_submit():
        # create an user instance not yet stored in the database
        user = User(name=form.name.data, email=form.email.data, password=generate_password_hash(form.password.data))
        # Insert the record in our database and commit it
        db.session.add(user)
        db.session.commit()

        # Log the user in, as he now has an id
        session['user_id'] = user.id

        # flash will display a message to the user
        flash('Thanks for registering')
        # redirect user to the 'home' method of the user module.
        return redirect_back_or('game.home')
    return render_template_with_user("users/register.html", form=form, next=next_url)
