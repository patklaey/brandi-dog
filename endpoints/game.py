from main import app, db
from flask import jsonify, request
from DB.Game import Game
from DB.User import User
from DB.Team import Team
from DB.Round import Round
from DB.Set import Set
from flask_jwt_extended import jwt_required, get_jwt_identity
import constants, random
from threading import Lock

lock = Lock()


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
    if not request.json["name"]:
        return "game name required", 400
    name = request.json["name"]
    players = 4
    if request.json["players"]:
        players = request.json["players"]
    new_game = Game(name, user_id, players)
    db.session.add(new_game)
    db.session.commit()
    return jsonify({"id": new_game.id}), 201


@app.route('/games/<int:game_id>')
@jwt_required
def show_game(game_id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403
    db_game = Game.query.get(game_id)
    # users = copy.deepcopy(db_users)
    return jsonify(db_game.to_dict()), 200


@app.route('/games/<int:game_id>', methods=["DELETE"])
@jwt_required
def delete_game(game_id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user or not current_user.admin:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403
    db_game = Game.query.get(game_id)

    if not db_game:
        return jsonify({'error': {'msg': 'Game not found', 'code': 16, 'info': game_id}}), 404

    db.session.delete(db_game)
    db.session.commit()
    return '', 204


@app.route('/games/open')
def show_open_games():
    db_games = Game.query.filter_by(game_state="new")
    game_dict = []
    for game in db_games:
        game_dict.append(game.to_dict())
    return jsonify(game_dict), 200


@app.route('/games/<int:game_id>/join', methods=["GET"])
@jwt_required
def join_game(game_id):
    user_id = get_jwt_identity()
    game_to_join = Game.query.get(game_id)
    if not game_to_join:
        return jsonify({'error': {'msg': 'Game not found', 'code': 16, 'info': game_id}}), 404

    if game_to_join.players_joined == game_to_join.number_of_players:
        return jsonify({'error': {'msg': 'Game ' + str(game_id) + ' is already full', 'code': 16, 'info': game_id}}), 406

    if user_id in game_to_join.get_players():
        return jsonify({'error': {'msg': 'You already joined game  ' + str(game_id), 'code': 16, 'info': game_id}}), 409

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

    if game_to_join.players_joined != game_to_join.number_of_players:
        return jsonify({'error': {'msg': 'Game ' + str(game_id) + ' is not full, cannot build teams yet', 'code': 16, 'info': game_id}}), 406

    if game_to_join.set_team_building():
        db.session.commit()
        return '', 200
    else:
        db.session.rollback()
        return jsonify({'error': {'msg': 'Could not change game state for game ' + str(game_id), 'code': 16, 'info': game_id}}), 500


@app.route('/games/<int:game_id>/finish', methods=["GET"])
@jwt_required
def finish_game(game_id):
    user_id = get_jwt_identity()
    game_to_finish = Game.query.get(game_id)
    if not game_to_finish:
        return jsonify({'error': {'msg': 'Game not found', 'code': 16, 'info': game_id}}), 404

    if not game_to_finish.game_admin == user_id:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403

    if game_to_finish.finish_game():
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
    if game_to_join.number_of_players == 6 and not request.json["teamC"]:
        return jsonify({'error': {'msg': 'Game is for 6 players but only two teams provided', 'code': 24}}), 400

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
    if game_to_join.number_of_players == 6:
        team_c_json = request.json["teamC"]
        if not team_c_json["player1"] or not team_c_json["player2"]:
            return jsonify({'error': {'msg': 'Team C not complete', 'code': 24}}), 400
        if team_c_json["player1"] == team_c_json["player2"]:
            return jsonify({'error': {'msg': 'Team C players are not unique', 'code': 24}}), 400
        team_c = Team(game_id, team_c_json["player1"], team_c_json["player2"], "C")
        db.session.add(team_c)

    db.session.add(team_a)
    db.session.add(team_b)

    if game_to_join.number_of_players == 4:
        game_to_join.set_order_of_play([team_a_json["player1"], team_b_json["player1"], team_a_json["player2"], team_b_json["player2"]])
    else:
        game_to_join.set_order_of_play([team_a_json["player1"], team_b_json["player1"], team_c_json["player1"], team_a_json["player2"], team_b_json["player2"], team_c_json["player2"]])
    db.session.commit()
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
    game_to_start = Game.query.get(game_id)
    if not game_to_start:
        return jsonify({'error': {'msg': 'Game not found', 'code': 16, 'info': game_id}}), 404

    if not game_to_start.game_admin == user_id:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403

    if game_to_start.players_joined != game_to_start.number_of_players:
        return jsonify({'error': {'msg': 'Game ' + str(game_id) + ' is not full yet, cannot start game', 'code': 16, 'info': game_id}}), 406

    if game_to_start.set_in_progress():
        create_new_round(game_to_start, game_to_start.player0, 6)
        return '', 201
    else:
        db.session.rollback()
        return jsonify({'error': {'msg': 'Could not start game ' + str(game_id), 'code': 16, 'info': game_id}}), 500


@app.route('/games/<int:game_id>/currentRound', methods=["GET"])
@jwt_required
def get_current_round(game_id):
    user_id = get_jwt_identity()
    game = Game.query.get(game_id)
    if not check_player_in_game(user_id, game):
        return '', 403

    if game.game_state == constants.NEW:
        return '', 406

    current_round = game.get_current_round()
    return jsonify(current_round.to_dict()), 200


@app.route('/games/<int:game_id>/currentRound/set', methods=["GET"])
@jwt_required
def get_current_set(game_id):
    user_id = get_jwt_identity()
    game = Game.query.get(game_id)
    if not check_player_in_game(user_id, game):
        return '', 403

    if game.game_state == constants.NEW:
        return '', 406

    current_round = game.get_current_round()
    db_set = get_current_card_set(game_id, current_round.id, user_id)
    if db_set is None:
        return 'Multiple sets or no set found, something is wrong', 409
    else:
        return jsonify(db_set.to_dict()), 200


@app.route('/games/<int:game_id>/currentRound/changecard', methods=["POST"])
@jwt_required
def change_card(game_id):
    with lock:
        user_id = get_jwt_identity()
        game = Game.query.get(game_id)
        if not check_player_in_game(user_id, game):
            return '', 403

        current_round = game.get_current_round()
        if not current_round or current_round.round_state != constants.CHANGE_CARDS:
            return "It's not time to change cards now", 406

        card_to_exchange = request.json["card"]
        if card_to_exchange not in ["card1", "card2", "card3", "card4", "card5", "card6"]:
            return 'Invalid card' + card_to_exchange, 400

        db_set = get_current_card_set(game_id, current_round.id, user_id)
        if db_set is None:
            return 'Multiple sets or no set found, something is wrong', 409

        card_value = getattr(db_set, card_to_exchange)
        if card_value is None:
            return 'You little cheater', 406

        db_teams = Team.query.filter_by(game_id=game_id)
        for db_team in db_teams:
            if db_team.player1 == user_id:
                if db_team.player1_card_to_exchange:
                    return 'You have already set your card to exchange', 406
                db_team.player1_card_to_exchange = card_to_exchange
                if db_team.player2_card_to_exchange:
                    if not exchange_cards(db_team, current_round):
                        db.session.rollback()
                        return 'Cannot exchange cards', 500
            if db_team.player2 == user_id:
                if db_team.player2_card_to_exchange:
                    return 'You have already set your card to exchange', 406
                db_team.player2_card_to_exchange = card_to_exchange
                if db_team.player1_card_to_exchange:
                    if not exchange_cards(db_team, current_round):
                        db.session.rollback()
                        return 'Cannot exchange cards', 500

        db.session.commit()
        return '', 200


@app.route('/games/<int:game_id>/currentRound/playcard', methods=["POST"])
@jwt_required
def play_card(game_id):
    user_id = get_jwt_identity()
    game = Game.query.get(game_id)
    if not check_player_in_game(user_id, game):
        return '', 403

    if game.game_state == constants.NEW:
        return '', 406

    current_round = game.get_current_round()
    if current_round.player_to_play != user_id:
        return 'Not your turn! Patience please!', 406

    card = request.json["card"]
    if card not in ["card1", "card2", "card3", "card4", "card5", "card6"]:
        return 'Invalid card' + card, 400

    db_set = get_current_card_set(game_id, current_round.id, user_id)
    if db_set is None:
        return 'Multiple sets or no set found, something is wrong', 409

    card_value = getattr(db_set, card)
    if card_value is None:
        return 'You little cheater', 406

    current_round.last_card_played = card_value
    setattr(db_set, card, None)
    db_set.reduce_cards_left()
    next_player = get_next_player(game, user_id)
    current_round.player_to_play = next_player

    if round_is_over(game_id, current_round):
        new_initial_player = get_next_player(game, current_round.player_to_play)
        current_round_cards = current_round.cards_to_play
        if current_round_cards == 2:
            new_round_cards = 6
        else:
            new_round_cards = current_round_cards - 1
        create_new_round(game, new_initial_player, new_round_cards)
        current_round.next_stage()

    db.session.commit()
    return '', 200


def round_is_over(game_id, current_round):
    db_set = get_current_card_set(game_id, current_round.id, current_round.player_to_play)
    return db_set.cards_left == 0


def get_next_player(game, user_id):
    players = game.get_players()
    player_index = players.index(user_id)
    next_player = players[(player_index + 1) % len(players)]
    return next_player


def generate_card_set(number_of_players, cards_to_play):
    round_set = random.sample(constants.INITIAL_SET, len(constants.INITIAL_SET))
    players_set = []
    for x in range(number_of_players):
        players_set.append([])
    card_number = 0
    for x in range(cards_to_play):
        for n in range(number_of_players):
            players_set[n].append(round_set[card_number])
            card_number += 1
    return players_set


def get_current_card_set(game_id, round_id, player_id):
    db_sets = db.session.query(Set).filter(Set.game_id == game_id, Set.round_id == round_id, Set.player_id == player_id).all()
    if len(db_sets) != 1:
        return None
    else:
        return db_sets[0]


def check_player_in_game(player_id, game):
    return game.player_is_in_game(player_id)


def create_new_round(game, initial_player, cards_to_play):
    new_round = Round(game.id, initial_player, cards_to_play)
    db.session.add(new_round)
    db.session.commit()
    players_set = generate_card_set(game.players_joined, new_round.cards_to_play)
    players = game.get_players()
    for x in range(game.players_joined):
        new_set = Set(game.id, new_round.id, players[x], players_set[x])
        db.session.add(new_set)
    new_round.next_stage()
    db.session.commit()


def exchange_cards(team, current_round):
    player1_set = db.session.query(Set).filter(Set.round_id == current_round.id, Set.player_id == team.player1).all()
    player2_set = db.session.query(Set).filter(Set.round_id == current_round.id, Set.player_id == team.player2).all()
    if len(player1_set) != 1 or len(player2_set) != 1:
        return False

    player1_card_value = getattr(player1_set[0], team.player1_card_to_exchange)
    player2_card_value = getattr(player2_set[0], team.player2_card_to_exchange)
    setattr(player1_set[0], team.player1_card_to_exchange, player2_card_value)
    setattr(player2_set[0], team.player2_card_to_exchange, player1_card_value)
    team.player1_card_to_exchange = None
    team.player2_card_to_exchange = None
    current_round.team_exchanged_cards()
    return True


