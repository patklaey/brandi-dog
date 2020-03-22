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
    db.session.add(admin)
    pat = User('pat', 'password', 'pat@247.ch', "en", False, True)
    db.session.add(pat)
    db.session.commit()
    click.echo("Done")


@app.cli.command()
def addgame():
    game = Game(1)
    db.session.add(game)
    db.session.commit()
    click.echo("Done")


@app.cli.command()
def cleandb():
    db.drop_all()
    click.echo("Tables dropped")
