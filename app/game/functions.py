from app import db


def make_turn(turn_id, game, user):
    if user != game.current_user:
        raise AttributeError("It is not the users turn.")

    possible_turns = game.get_possible_turns(user)

    if turn_id >= len(possible_turns):
        raise RuntimeError("Turn is not possible.")

    turn = possible_turns[turn_id]
    turn.set_turn_properties()

    db.session.add(turn)
    # TODO: Do we need a commit here?

    game.update_game_status()
    db.session.merge(game)

    db.session.commit()


class CachedClassFunction:
    def __init__(self, variable_name=None):
        self._variable_value = None
        self._variable_name = variable_name

    def invalidate_cache(self, instance):
        instance._cache = {}
        self._variable_value = None

    def __call__(self, f):
        self.f = f

        def wrapped_f(instance, *args, **kwargs):

            args_string = str(args)
            kwargs_string = str(kwargs)

            if self._variable_name:
                current_variable_value = getattr(instance, self._variable_name)
                if self._variable_value and current_variable_value != self._variable_value:
                    self.invalidate_cache(instance)

                self._variable_value = current_variable_value

            try:
                cache = getattr(instance, "_cache" + f.__name__)
            except AttributeError:
                setattr(instance, "_cache" + f.__name__, {})
                cache = getattr(instance, "_cache" + f.__name__)

            try:
                value = cache[(args_string, kwargs_string)]
            except KeyError:
                value = f(instance, *args, **kwargs)
                cache[(args_string, kwargs_string)] = value
            return value

        wrapped_f.__name__ = f.__name__
        wrapped_f.__doc__ = f.__doc__
        wrapped_f.__module__ = f.__module__

        return wrapped_f


class CachedClassProperty(CachedClassFunction):
    def __call__(self, f):
        self._wrapped_f = CachedClassFunction.__call__(self, f)
        return self

    def __get__(self, inst, owner):
        return self._wrapped_f(inst)
