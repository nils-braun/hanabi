from app import app, db
from app.users.models import User

db.create_all()

user = User(u"test", "test@test.com", "pbkdf2:sha1:1000$VUu0UWDW$211afd0957df48d23553a119668dbc331b84c8cd")
db.session.add(user)

user_2 = User(u"test2", "test2@test.com", "pbkdf2:sha1:1000$VUu0UWDW$211afd0957df48d23553a119668dbc331b84c8cd")
db.session.add(user_2)
db.session.commit()

app.run(debug=True)
