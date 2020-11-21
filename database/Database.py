import os

import sqlite3
from flask import g, current_app
from flask.cli import with_appcontext
import click

from config import BASE_DIR

from typing import Optional


class Database():

    db: sqlite3.Connection = None

    database_path = 'namesrelationship.db'
    schema_path = 'schema.sql'

    @property
    def cursor(self):
        return self.db.cursor()

    def __init__(self):
        self.init_db()

    def init_db(self):

        self.db = self.db or self.connect()

        with current_app.open_resource(os.path.join('database', self.schema_path)) as f:
        # with open(os.path.join(BASE_DIR, 'database', self.schema_path), 'r') as f:
            self.db.executescript(f.read().decode('utf8'))
        # 
        # with app.app_context():
        # with app.open_resource('schema.sql', mode='r') as f:
        #     db.cursor().executescript(f.read())
        # db.commit()

    @click.command('init-db')
    @with_appcontext
    def init_db_command(self):
        self.init_db()
        click.echo('Initialized the database.')

    def connect(self):
        if 'db' not in g:
            g.db = sqlite3.connect(
                current_app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
                )
        g.db.row_factory = sqlite3.Row
        self.db: sqlite3.Connection = g.db
        return self.db

    def close_db(self, exception: Optional[Exception] = None):
        db = g.pop('db', None)

        if db is not None:
            db.close()
            self.db = None

    def init_app(self, app):
        app.teardown_appcontext(self.close_db)
        app.cli.add_command(self.init_db_command)
