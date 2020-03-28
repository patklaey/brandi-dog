import click

from main import app, db
from DB.User import User
from DB.Game import Game


@app.cli.command()
def initdb():
    """Initialize the database."""
    db.create_all()
    click.echo('Init the db')


@app.cli.command()
def addusers():
    admin = User('admin', 'admin', 'kly7@247.ch', "en", True, True)
    pat = User('pat', 'password', 'pat@247.ch', "en", False, True)
    player1 = User('player1', 'password', 'player1@247.ch', "en", False, True)
    player2 = User('player2', 'password', 'player2@247.ch', "en", False, True)
    db.session.add(admin)
    db.session.add(pat)
    db.session.add(player1)
    db.session.add(player2)
    db.session.commit()
    click.echo("Done")


@app.cli.command()
def addgame():
    game = Game("Test", 1)
    db.session.add(game)
    db.session.commit()
    click.echo("Done")


@app.cli.command()
def joingame():
    game = Game.query.first()
    game.join_game(2)
    game.join_game(3)
    game.join_game(4)
    db.session.commit()


@app.cli.command()
def cleandb():
    db.drop_all()
    click.echo("Tables dropped")


@app.cli.command()
@click.pass_context
def reset(ctx):
    ctx.invoke(cleandb)
    ctx.invoke(initdb)
    ctx.invoke(addusers)
    ctx.invoke(addgame)
    click.echo("All Done")
