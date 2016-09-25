from flask import Blueprint

from app.functions import render_template_with_user, add_before_request

mod = Blueprint('game', __name__, url_prefix='/game')
add_before_request(mod)


@mod.route('/home/', methods=['GET', 'POST'])
def home():
    return render_template_with_user("base.html")
