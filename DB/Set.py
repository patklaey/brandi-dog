from main import db


class Set(db.Model):
    __tablename__ = 'sets'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'))
    player_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    card1 = db.Column(db.String(2))
    card2 = db.Column(db.String(2))
    card3 = db.Column(db.String(2))
    card4 = db.Column(db.String(2))
    card5 = db.Column(db.String(2))
    card6 = db.Column(db.String(2))
    cards_left = db.Column(db.Integer)

    def __init__(self, game_id, round_id, player_id, cards):
        self.game_id = game_id
        self.round_id = round_id
        self.player_id = player_id
        self.card1 = cards[0]
        self.card2 = cards[1]
        if len(cards) >= 3:
            self.card3 = cards[2]
        if len(cards) >= 4:
            self.card4 = cards[3]
        if len(cards) >= 5:
            self.card5 = cards[4]
        if len(cards) >= 6:
            self.card6 = cards[5]
        self.cards_left = len(cards)

    def to_dict(self):
        dict = self.__dict__
        if '_sa_instance_state' in dict:
            del dict['_sa_instance_state']
        dict["cards"] = []
        if self.card1:
            dict["cards"].append({"key": "card1", "value": self.card1})
        if self.card2:
            dict["cards"].append({"key": "card2", "value": self.card2})
        if self.card3:
            dict["cards"].append({"key": "card3", "value": self.card3})
        if self.card4:
            dict["cards"].append({"key": "card4", "value": self.card4})
        if self.card5:
            dict["cards"].append({"key": "card5", "value": self.card5})
        if self.card6:
            dict["cards"].append({"key": "card6", "value": self.card6})
        return dict

    def reduce_cards_left(self):
        if self.cards_left > 0:
            self.cards_left = self.cards_left - 1
