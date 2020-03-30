import smtplib
import copy
from email.mime.text import MIMEText
from main import app, db
from flask import jsonify, request
from DB.User import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from constants import MAIL_MESSAGES, PASSWORD_MIN_LENGTH


@app.route('/users')
@jwt_required
def show_users():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    db_users = User.query.all()
    users = copy.deepcopy(db_users)
    userDict = []
    for user in users:
        if not current_user or not current_user.admin:
            userDict.append({"id": user.id, "username": user.username})
        else:
            userDict.append(user.to_dict())
    return jsonify(userDict), 200


@app.route('/users/<int:id>', methods=["GET"])
@jwt_required
def show_user(id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    if not current_user.admin and id != user_id_from_token:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403
    user = User.query.get(id)
    if user is not None:
        return jsonify(copy.deepcopy(user).to_dict())
    else:
        return jsonify({'error': {'msg': 'User not found', 'code': 16, 'info': id}}), 404


@app.route('/users/<int:user_id>', methods=["PUT", "PATCH"])
@jwt_required
def edit_user(user_id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    if not current_user.admin and user_id != user_id_from_token:
        return jsonify({'error': {'msg': 'Operation not permitted', 'code': 14}}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': {'msg': 'User not found', 'code': 16, 'info': user_id}}), 404

    if "password" in request.json and not current_user.admin:
        if "oldPassword" not in request.json:
            return jsonify({'error': {'msg': 'Current password must be provided as "oldPassword" within the request body', 'code': 21}}), 400
        if not user.verify_password(request.json["oldPassword"]):
            return jsonify({'error': {'msg': 'Password missmatch for user', 'code': 22}}), 401

    try:
        if "password" in request.json:
            if len(request.json['password']) < PASSWORD_MIN_LENGTH:
                return jsonify({'error': {'msg': 'Password needs to be at least 8 characters long', 'code': 24}}), 400
            user.hash_password(request.json["password"])
            del request.json["password"]
        for attribute in request.json:
            if attribute in User.get_protected_attributes() and not current_user.admin:
                db.session.rollback()
                return jsonify({'error': {'msg': 'Attribute protected', 'code': 23}}), 400
            if attribute in User.get_all_attributes():
                setattr(user, attribute, request.json[attribute])
        db.session.commit()
        return '', 204
    except Exception:
        db.session.rollback()
        return jsonify({"error": {'msg': "Failed to update user", 'code': 17}}), 500


@app.route('/users', methods=["POST"])
def add_user():
    for attribute in User.get_required_attributes():
        if attribute not in request.json:
            return jsonify({'error': {'msg': '\'' + attribute + '\' is required', 'code': 2, 'info': attribute}}), 400
    if len(request.json['password']) < PASSWORD_MIN_LENGTH:
        return jsonify({'error': {'msg': 'Password needs to be at least 8 characters long', 'code': 24}}), 400
    data = request.json
    username_exists = User.query.filter_by(username=data['username']).first()
    if username_exists:
        return jsonify({'error': {'msg': 'Username ' + data['username'] + ' is already taken, please choose a different one', 'code': 24}}), 409

    email_exists = User.query.filter_by(email=data['email']).first()
    if email_exists:
        return jsonify({'error': {'msg': 'There ia already a user registered with email ' + data['email'], 'code': 24}}), 409

    new_user = User(data['username'], data['password'], data['email'], data['language'], admin=False, active=True)
    db.session.add(new_user)
    db.session.commit()
    send_new_user_mail(new_user)
    return '', 201


@app.route('/users/<int:user_id>', methods=["DELETE"])
@jwt_required
def delete_user(user_id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    if not current_user.admin:
        return jsonify({'error': {'msg': 'Operation not permitted', 'code': 14}}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': {'msg': 'User not found', 'code': 16, 'info': user_id}}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return '', 204
    except Exception as error:
        # Log error
        return jsonify({"error": {'msg': "Cannot delete user", 'code': 18}}), 500


@app.route('/users/checkUnique', methods=["GET"])
def check_unique_attribute():
    arguments = request.args
    possible_keys = ['username', 'email']
    if 'key' not in arguments or 'value' not in arguments:
        return jsonify({'error': {'msg': '"key" and "value" must be given as query parameters', 'code': 19}}), 400
    if not arguments['key'] in possible_keys:
        return jsonify({'error': {'msg': '"key" can be one of the following: ' + ",".join(possible_keys), 'code': 20,
                                  'info': ",".join(possible_keys)}}), 400
    kwargs = {arguments['key']: arguments['value']}
    user = User.query.filter_by(**kwargs).first()
    if not user:
        return jsonify({'unique': True}), 200
    else:
        return jsonify({'unique': False}), 200


def send_new_user_mail(user):
    mail_host = app.config['MAIL_HOST']
    mail_port = app.config['MAIL_PORT']
    mail_user = app.config['MAIL_LOGIN_USER']
    mail_pass = app.config['MAIL_LOGIN_PASS']
    mailer = smtplib.SMTP_SSL(mail_host, mail_port)
    mailer.login(mail_user, mail_pass)
    send_new_user_information_mail(user, mailer)
    mailer.quit()


def send_new_user_information_mail(user, mailer):
    mail_to = user.email
    mail_from = app.config['MAIL_FROM']
    mail_messaage = MAIL_MESSAGES[user.language]['registration']['message'].format(user.username)
    message = MIMEText(mail_messaage)
    message["Subject"] = MAIL_MESSAGES[user.language]['registration']['subject']
    message["From"] = mail_from
    message["To"] = mail_to
    mailer.sendmail(mail_from, mail_to, message.as_string())

