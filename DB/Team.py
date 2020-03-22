from main import db


class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    player1 = db.Column(db.Integer, db.ForeignKey('users.id'))
    player2 = db.Column(db.Integer, db.ForeignKey('users.id'))
    team_name = db.Column(db.String(120))

    def __init__(self, game_id, player1, player2, team_name):
        self.game_id = game_id
        self.player1 = player1
        self.player2 = player2
        self.team_name = team_name

    def to_dict(self):
        dict = self.__dict__
        if '_sa_instance_state' in dict:
            del dict['_sa_instance_state']
        return dict