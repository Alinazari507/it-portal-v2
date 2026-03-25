from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, role, fullname, department):
        self.id = id
        self.username = username
        self.role = role
        self.fullname = fullname
        self.department = department