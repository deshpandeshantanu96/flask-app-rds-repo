from flask import Flask
from app.database import init_db
from app.routes import bp

def create_app():
    app = Flask(__name__)
    init_db(app)
    app.register_blueprint(bp)
    return app