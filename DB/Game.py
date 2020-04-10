from main import db
from threading import Lock
from DB.Round import Round
from constants import NEW,TEAM_BUILDING,IN_PROGRESS,FINISHED


lock = Lock()


class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(120))
    game_admin = db.Column(db.Integer, db.ForeignKey('users.id'))
    game_state = db.Column(db.String(120))
    players_joined = db.Column(db.Integer)
    number_of_players = db.Column(db.Integer)
    player0 = db.Column(db.Integer, db.ForeignKey('users.id'))
    player1 = db.Column(db.Integer, db.ForeignKey('users.id'))
    player2 = db.Column(db.Integer, db.ForeignKey('users.id'))
    player3 = db.Column(db.Integer, db.ForeignKey('users.id'))
    player4 = db.Column(db.Integer, db.ForeignKey('users.id'))
    player5 = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, game_name, game_admin, number_of_players=4):
        self.game_admin = game_admin
        self.game_name = game_name
        self.game_state = NEW
        self.player0 = game_admin
        self.players_joined = 1
        self.number_of_players = number_of_players

    def to_dict(self):
        dict = self.__dict__
        if '_sa_instance_state' in dict:
            del dict['_sa_instance_state']
        dict["players"] = [self.player0, self.player1, self.player2, self.player3]
        if self.number_of_players == 6:
            dict["players"].append(self.player4)
            dict["players"].append(self.player5)
        return dict

    def get_players(self):
        players = [self.player0, self.player1, self.player2, self.player3]
        if self.number_of_players == 6:
            players.append(self.player4)
            players.append(self.player5)
        return players

    def set_order_of_play(self, order_of_play):
        self.player0 = order_of_play[0]
        self.player1 = order_of_play[1]
        self.player2 = order_of_play[2]
        self.player3 = order_of_play[3]
        if len(order_of_play) == 6:
            self.player4 = order_of_play[4]
            self.player5 = order_of_play[5]

    def get_current_round(self):
        rounds = db.session.query(Round).filter(Round.game_id == self.id, Round.round_state != FINISHED).all()
        if len(rounds) != 1:
            return None
        else:
            return rounds[0]

    def join_game(self, player_id):
        with lock:
            if self.players_joined == self.number_of_players:
                return False
            self.players_joined += 1
            if not self.player1:
                self.player1 = player_id
            elif not self.player2:
                self.player2 = player_id
            elif not self.player3:
                self.player3 = player_id
            elif not self.player4:
                self.player4 = player_id
            elif not self.player5:
                self.player5 = player_id
            return True

    def set_team_building(self):
        if not (self.game_state == NEW or self.game_state == TEAM_BUILDING) or self.players_joined != self.number_of_players:
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
