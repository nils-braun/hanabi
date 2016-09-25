from flask_wtf import Form
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, EqualTo, NumberRange, ValidationError

from app.users.models import User


class StartPlayerValidator(object):
    def __call__(self, form, field):
        data = field.data
        if data is None or data not in map(lambda x: x.strip(), form.users.data.split(",")):
            raise ValidationError("Start player must be in the game.")


class PlayerValidator(object):
    def __call__(self, form, field):
        data = field.data
        if data is not None:
            for user in data.split(","):
                if User.query.filter_by(name=user.strip()).count() != 1:
                    raise ValidationError("Invalid user {user}.".format(user=user))


class NewGameForm(Form):
    users = StringField('Users', [DataRequired(), PlayerValidator()])
    start_failures = IntegerField('Failures', [DataRequired(), NumberRange(0, 5)], default=3)
    start_hints = IntegerField('Hints', [DataRequired(), NumberRange(0, 12)], default=10)
    start_player = StringField('Start Player', [DataRequired(), StartPlayerValidator()])
