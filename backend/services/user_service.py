from sqlalchemy.orm import Session

class User_Service:
    def __init__(self, db: Session):
        self.db = db

    def register_new_user(self, username: str, password: str):
        # Check if the user already exists in the database
        pass