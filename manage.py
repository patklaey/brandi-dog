from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from main import app, db


app.config.from_pyfile('./config/config.py')

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()

"""
Execute the following commands to migrate the DB:

python manage.py db init

python manage.py db migrate

python manage.py db upgrade

"""