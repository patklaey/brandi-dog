from main import db
from constants import NEW, CHANGE_CARDS, IN_PROGRESS, FINISHED


class Round(db.Model):
    __tablename__ = 'rounds'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    round_state = db.Column(db.String(120))
    initial_player = db.Column(db.Integer, db.ForeignKey('users.id'))
    player_to_play = db.Column(db.Integer, db.ForeignKey('users.id'))
    cards_to_play = db.Column(db.Integer)
    last_card_played = db.Column(db.String(2))
    teams_cards_exchanged = db.Column(db.Integer)

    def __init__(self, game_id, initial_player, card_to_play):
        self.game_id = game_id
        self.initial_player = initial_player
        self.player_to_play = initial_player
        self.round_state = NEW
        self.cards_to_play = card_to_play
        self.teams_cards_exchanged = 0

    def to_dict(self):
        dict = self.__dict__
        if '_sa_instance_state' in dict:
            del dict['_sa_instance_state']
        return dict

    def set_last_card_played(self, card_value):
        self.last_card_played = card_value

    def next_stage(self):
        if self.round_state == NEW:
            self.round_state = CHANGE_CARDS
        elif self.round_state == CHANGE_CARDS:
            self.round_state = IN_PROGRESS
        elif self.round_state == IN_PROGRESS:
            self.round_state = FINISHED

    def team_exchanged_cards(self):
        self.teams_cards_exchanged = self.teams_cards_exchanged + 1
        game = Game.query.get(self.game_id)
        if self.teams_cards_exchanged == (game.number_of_players / 2):
            self.next_stage()
