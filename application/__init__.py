from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)
from application import routes,models



if __name__ == '__main__':
    socketio.run(app)