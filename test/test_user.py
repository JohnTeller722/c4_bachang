import unittest
from app import create_app, db
from app.models.user import User, Role

class UserModelTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self) -> None:
        role = Role(name='Admin', description='Administrator')
        db.session.add(role)
        db.session.commit()

        user = User(
            email='test@example.com',
            password='password',
            active=True,
            fs_uniquifier='unique123',
            roles=[role],
            avatar='avatar.jpg',
            experience=10,
            level=1
        )
        db.session.add(user)
        db.session.commit()

        retrieved_user = User.query.filter_by(email='test@example.com').first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, 'test@example.com')
        self.assertEqual(retrieved_user.roles[0].name, 'Admin')

if __name__ == '__main__':
    unittest.main()