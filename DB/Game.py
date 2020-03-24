from main import db
from threading import Lock
from DB.Round import Round
from constants import NEW,TEAM_BUILDING,IN_PROGRESS,FINISHED


lock = Lock()


class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    game_admin = db.Column(db.Integer, db.ForeignKey('users.id'))
    game_state = db.Column(db.String(120))
    players_joined = db.Column(db.Integer)
    player0 = db.Column(db.Integer, db.ForeignKey('users.id'))
    player1 = db.Column(db.Integer, db.ForeignKey('users.id'))
    player2 = db.Column(db.Integer, db.ForeignKey('users.id'))
    player3 = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_card_played = db.Column(db.String(2))

    def __init__(self, game_admin):
        self.game_admin = game_admin
        self.game_state = NEW
        self.player0 = game_admin
        self.players_joined = 1

    def to_dict(self):
        dict = self.__dict__
        if '_sa_instance_state' in dict:
            del dict['_sa_instance_state']
        return dict

    def get_players(self):
        players = [self.player0, self.player1, self.player2, self.player3]
        return players

    def get_current_round(self):
        rounds = db.session.query(Round).filter(Round.game_id == self.id, Round.round_state != FINISHED).all()
        if len(rounds) != 1:
            return None
        else:
            return rounds[0]

    def join_game(self, player_id):
        with lock:
            if self.players_joined == 4:
                return False
            self.players_joined += 1
            if not self.player1:
                self.player1 = player_id
            elif not self.player2:
                self.player2 = player_id
            elif not self.player3:
                self.player3 = player_id
            return True

    def set_team_building(self):
        if self.game_state != NEW or self.players_joined != 4:
            return False
        else:
            self.game_state = TEAM_BUILDING
            return True

    def set_in_progress(self):
        if self.game_state != TEAM_BUILDING:
            return False
        else:
            self.game_state = IN_PROGRESS
            return True

    def finish_game(self):
        if self.game_state != IN_PROGRESS:
            return False
        else:
            self.game_state = FINISHED
            return True

    def player_is_in_game(self, player_id):
        return self.get_players().__contains__(player_id)

    def set_last_card_played(self, card_value):
        self.last_card_played = card_value