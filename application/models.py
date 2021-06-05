from application import db
import enum

class Team(enum.Enum):
    RED = 'red'
    BLUE = 'blue'

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    team = db.Column(db.Enum(Team))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    order = db.Column(db.Integer)
    def __repr__(self):
        return '<Player {id}, {name}, {team}>'.format(id=self.id, name=self.name, teeam=self.team)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    players = db.relationship('Player', backref='game', lazy=True)
    def __repr__(self):
        return '<Game {id}, {players}>'.format(id=self.id, players=self.players)