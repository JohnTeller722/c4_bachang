import unittest
from app import create_app, db
from app.models.user import User, Role

class UserAuthTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Check if the role already exists
        role = Role.query.filter_by(name='Admin').first()
        if not role:
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
        user.set_password('password')  # 使用加密方法设置密码
        db.session.add(user)
        db.session.commit()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login(self) -> None:
        response = self.client.post('/api/user/login', data={
            'username': 'test@example.com',
            'password': 'password'
        })
        print(response.get_data(as_text=True))  # 打印响应内容
        self.assertEqual(response.status_code, 200)
        content = response.get_json()  # 打印响应内容
        print(content)
        self.assertEqual(content["status"], 200)
        self.assertEqual(content["message"], "OK!")

    def test_login_invalid_credentials(self) -> None:
        response = self.client.post('/api/user/login', data={
            'username': 'test@example.com',
            'password': 'wrongpassword'
        })
        content = response.get_json()  # 打印响应内容
        print(content)
        self.assertEqual(content["status"], 401)
        self.assertEqual(content["message"], "凭据错误，登录失败！请检查你的用户名或密码。")

    # def test_logout(self) -> None:
    #     self.client.post('/api/user/login', data={
    #         'username': 'test@example.com',
    #         'password': 'password'
    #     })
    #     response = self.client.post('/api/user/logout')
    #     print(response.get_data(as_text=True))  # 打印响应内容
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json, {"status": 200, "message": "登出成功"})

    # def test_status(self) -> None:
    #     self.client.post('/api/user/login', data={
    #         'username': 'test@example.com',
    #         'password': 'password'
    #     })
    #     response = self.client.get('/api/user/status')
    #     print(response.get_data(as_text=True))  # 打印响应内容
    #     self.assertEqual(response.status_code, 200)
    #     user_info = response.json
    #     print(user_info)  # 打印响应内容
    #     self.assertEqual(user_info['email'], 'test@example.com')
    #     self.assertEqual(user_info['roles'][0], 'Admin')
    #     self.assertEqual(user_info['avatar'], 'avatar.jpg')
    #     self.assertEqual(user_info['experience'], 10)
    #     self.assertEqual(user_info['level'], 1)

if __name__ == '__main__':
    unittest.main()