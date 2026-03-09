from app import app
from models import User

with app.app_context():
    users = User.query.order_by(User.id).all()
    print(f'total users: {len(users)}')
    for u in users:
        print(u.id, u.username, u.role, 'actif=' + str(u.actif))
