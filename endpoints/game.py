from main import app, db
from flask import jsonify, request
from DB.Game import Game
from DB.User import User
from DB.Team import Team
from flask_jwt_extended import jwt_required, get_jwt_identity


@app.route('/games')
@jwt_required
def show_games():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403
    db_games = Game.query.all()
    # users = copy.deepcopy(db_users)
    game_dict = []
    for game in db_games:
        game_dict.append(game.to_dict())
    return jsonify(game_dict)


@app.route('/games', methods=["POST"])
@jwt_required
def create_games():
    user_id = get_jwt_identity()
    new_game = Game(user_id)
    db.session.add(new_game)
    db.session.commit()
    return '', 201


@app.route('/games/<int:game_id>')
@jwt_required
def show_game(game_id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403
    db_game = Game.query.get(game_id)
    # users = copy.deepcopy(db_users)
    return jsonify(db_game)


@app.route('/games/open')
@jwt_required
def show_open_games():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403
    db_games = Game.query.filter_by(game_state="new")
    # users = copy.deepcopy(db_users)
    game_dict = []
    for game in db_games:
        game_dict.append(game.to_dict())
    return jsonify(game_dict)


@app.route('/games/<int:game_id>/join', methods=["GET"])
@jwt_required
def join_game(game_id):
    user_id = get_jwt_identity()
    game_to_join = Game.query.get(game_id)
    if not game_to_join:
        return jsonify({'error': {'msg': 'Game not found', 'code': 16, 'info': game_id}}), 404

    if game_to_join.players_joined == 4:
        return jsonify({'error': {'msg': 'Game ' + str(game_id) + ' is already full', 'code': 16, 'info': game_id}}), 406

    if game_to_join.join_game(user_id):
        db.session.commit()
        return '', 200
    else:
        db.session.rollback()
        return jsonify({'error': {'msg': 'Could not join game ' + str(game_id), 'code': 16, 'info': game_id}}), 500


@app.route('/games/<int:game_id>/buildteams', methods=["GET"])
@jwt_required
def build_teams(game_id):
    user_id = get_jwt_identity()
    game_to_join = Game.query.get(game_id)
    if not game_to_join:
        return jsonify({'error': {'msg': 'Game not found', 'code': 16, 'info': game_id}}), 404

    if not game_to_join.game_admin == user_id:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403

    if game_to_join.players_joined != 4:
        return jsonify({'error': {'msg': 'Game ' + str(game_id) + ' is not full, cannot build teams yet', 'code': 16, 'info': game_id}}), 406

    if game_to_join.set_team_building():
        db.session.commit()
        return '', 200
    else:
        db.session.rollback()
        return jsonify({'error': {'msg': 'Could not change game state for game ' + str(game_id), 'code': 16, 'info': game_id}}), 500


@app.route('/games/<int:game_id>/teams', methods=["POST"])
@jwt_required
def create_teams(game_id):
    user_id = get_jwt_identity()
    game_to_join = Game.query.get(game_id)
    if not game_to_join:
        return jsonify({'error': {'msg': 'Game not found', 'code': 16, 'info': game_id}}), 404

    if not game_to_join.game_admin == user_id:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403

    if not request.json["teamA"] or not request.json["teamB"]:
        return jsonify({'error': {'msg': 'Both teams are required', 'code': 24}}), 400

    team_a_json = request.json["teamA"]
    team_b_json = request.json["teamB"]

    if not team_a_json["player1"] or not team_a_json["player2"]:
        return jsonify({'error': {'msg': 'Team A not complete', 'code': 24}}), 400
    if not team_b_json["player1"] or not team_b_json["player2"]:
        return jsonify({'error': {'msg': 'Team B not complete', 'code': 24}}), 400
    if team_a_json["player1"] == team_a_json["player2"]:
        return jsonify({'error': {'msg': 'Team A players are not unique', 'code': 24}}), 400
    if team_b_json["player1"] == team_b_json["player2"]:
        return jsonify({'error': {'msg': 'Team B players are not unique', 'code': 24}}), 400

    team_a = Team(game_id, team_a_json["player1"], team_a_json["player2"], "A")
    team_b = Team(game_id, team_b_json["player1"], team_b_json["player2"], "B")
    db.session.add(team_a)
    db.session.add(team_b)
    db.session.commit()
    # TODO: start game automatically
    return '', 201


@app.route('/games/<int:game_id>/teams', methods=["GET"])
@jwt_required
def get_teams(game_id):
    db_teams = Team.query.filter_by(game_id=game_id)
    team_map = {}
    for team in db_teams:
        team_map[team.team_name] = {"player1": team.player1, "player2": team.player2}
    return jsonify(team_map), 200


@app.route('/games/<int:game_id>/start', methods=["GET"])
@jwt_required
def start_game(game_id):
    user_id = get_jwt_identity()
    game_to_join = Game.query.get(game_id)
    if not game_to_join:
        return jsonify({'error': {'msg': 'Game not found', 'code': 16, 'info': game_id}}), 404

    if not game_to_join.game_admin == user_id:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403

    if game_to_join.players_joined != 4:
        return jsonify({'error': {'msg': 'Game ' + str(game_id) + ' is not full yet, cannot start game', 'code': 16, 'info': game_id}}), 406

    if game_to_join.set_in_progress():
        db.session.commit()
        return '', 200
    else:
        db.session.rollback()
        return jsonify({'error': {'msg': 'Could not start game ' + str(game_id), 'code': 16, 'info': game_id}}), 500


