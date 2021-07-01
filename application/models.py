from application import db
import enum
from sqlalchemy.ext.mutable import MutableDict

class Team(enum.Enum):
    RED = 'red'
    BLUE = 'blue'

class CardSuite(enum.Enum):
    SPADE ='spades'
    HEART = 'hearts'
    CLUB = 'clubs'
    DIAMOND = 'diamonds'
    NOTRUMP = 'no_trump'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, CardSuite))

class CardNumber(enum.Enum):
    JACK = {'name':'jack', 'number':11, 'points':3, 'priority':7}
    NINE = {'name':'9','number':9, 'points':2, 'priority':6}
    ACE = {'name':'ace', 'number':14, 'points':1, 'priority':5}
    TEN = {'name':'10', 'number':10,'points':1, 'priority':4}
    KING = {'name':'king', 'number':13, 'points':0, 'priority':3}
    QUEEN = {'name':'queen', 'number':12, 'points':0, 'priority':2}
    EIGHT = {'name':'8', 'number':8, 'points':0, 'priority':1}
    SEVEN = {'name':'7', 'number':7, 'points':0, 'priority':0}

    @staticmethod
    def list():
        return list(map(lambda c: c.value, CardNumber))

    @staticmethod
    def get_by_number(n):
        for c in CardNumber:
            if c.value['number'] == n:
                return c


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    team = db.Column(db.Enum(Team))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    order = db.Column(db.Integer)
    deck = db.relationship('Card', backref='player')

    def __repr__(self):
        return '{id}, {name}, {team}'.format(id=self.id, name=self.name, team=self.team.value)

    def as_dict(self):
        d = []
        for c in self.deck:
            d.append(c.as_dict())
        obj_d = {
            'id':self.id,
            'name':self.name,
            'team':self.team.value,
            'game_id':self.game_id,
            'order':self.order,
            'deck':d
        }
        return obj_d


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    players = db.relationship('Player', backref='game', lazy=True)
    red_score = db.Column(db.Integer, default=0)
    blue_score = db.Column(db.Integer, default=0)
    highest_bid = db.Column(db.Integer, default=16)
    bid_winner = db.Column(db.Enum(Team))
    trump = db.Column(db.Enum(CardSuite))
    trump_order = db.Column(db.Integer, default=0)
    bid_stack = db.Column(MutableDict.as_mutable(db.JSON), default={0:-1, 1:-1, 2:-1, 3:-1})
    double = db.Column(db.Integer, default=1)
    double_counter = db.Column(db.Integer, default=0)
    aukat_set = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Game {id}, {players}>'.format(id=self.id, players=self.players)
    def increment_highest_bid(self):
        self.highest_bid = self.highest_bid + 1
    def set_double(self):
        self.double = self.double * 2
    def increment_double_counter(self):
        self.double_counter = self.double_counter + 1


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    number = db.Column(db.Enum(CardNumber))
    suite = db.Column(db.Enum(CardSuite))
    def as_dict(self):
        obj_d = {
            'id':self.id,
            'name':self.number.value['name'],
            'number':self.number.value['number'],
            'suite':self.suite.value,
            'priority':self.number.value['priority'],
            'points':self.number.value['points']
        }
        return obj_d

