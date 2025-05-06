from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DB_URI
    db.init_app(app)
    with app.app_context():
        db.create_all()