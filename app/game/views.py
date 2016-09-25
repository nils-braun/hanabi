from flask import Blueprint
from flask import flash
from flask import g
from flask import request

from app import db
from app.functions import render_template_with_user, add_before_request, redirect_back_or
from app.game import constants
from app.game.forms import NewGameForm
from app.game.models import Game, UsersInGames
from app.users.models import User

mod = Blueprint('game', __name__, url_prefix='/game')
add_before_request(mod)


@mod.route('/home/', methods=['GET'])
def home():
    current_games = UsersInGames.query.filter_by(user=g.user)
    return render_template_with_user("game/home.html", current_games=list(enumerate(current_games)))


@mod.route('/new_game/', methods=['GET', 'POST'])
def new_game():
    form = NewGameForm(request.form)

    if form.validate_on_submit():
        start_deck = Game.get_random_start_deck()

        start_player = User.query.filter_by(name=form.start_player.data).one()
        users = [User.query.filter_by(name=user_name.strip()).one() for user_name in form.users.data.split(",")]

        new_game = Game(start_deck=start_deck, start_player=start_player,
                        start_failures=form.start_failures.data,
                        start_hints=form.start_hints.data,
                        start_number_of_cards=Game.get_start_number_of_cards_for_players(len(users)))
        new_game.users = users

        db.session.add(new_game)
        db.session.commit()

        return redirect_back_or('game.home')

    return render_template_with_user("game/new_game.html", form=form)


@mod.route('/game/', methods=['GET'])
def game():
    current_game = Game.query.filter_by(id=int(request.args["id"])).one()
    return render_template_with_user("game/game.html", game=current_game)


@mod.route('/start_game/', methods=['GET'])
def start_game():
    game_id = request.args["id"]
    current_game = Game.query.filter_by(id=int(game_id)).one()
    current_game.state = constants.GAME_STARTED

    db.session.merge(current_game)
    db.session.commit()

    return redirect_back_or("game.game", id=game_id)

