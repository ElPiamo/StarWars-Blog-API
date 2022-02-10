from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique = False, nullable = False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    favorites = db.relationship("Favorites", backref="user", uselist=True)

    @classmethod
    def create(cls, new_user):
        user = cls(**new_user)
        
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as error:
            db.session.rollback()
            print(error)
            return None

    def serialize(self):
        return {
            "name": self.name,
            "id": self.id,
            "email": self.email
        }

class Favorites(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    url = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint(
        "user_id",
        "url",
        name = "unique_favorite_user"
    ),)

    def serialize(self): 
        name_of_user = User.query.filter_by(id=self.id).first()
        return {
            "name": self.name,
            "id": self.id,
            "email": name_of_user.email if name_of_user else None
        }

    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
            return True
        except Exception as error: 
            db.session.rollback()
            return False