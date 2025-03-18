import pymongo
from pymongo import MongoClient
from datetime import datetime

import click
from flask import current_app
from flask import g



def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:

        client = MongoClient(current_app.config["MONGODB_URL"])
        g.mongodbClient = client
        g.db = client[current_app.config["MONGODB_DATABASE"]]

    return g.db


def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    mongodbClient = g.pop("mongodbClient", None)

    if mongodbClient is not None:
        mongodbClient.close()


def init_db():
    """Clear existing data and create new collections."""
    db = get_db()

    db.user.drop()
   
    db.user.create_index("username", unique=True)
    db.user.create_index("email", unique=True)
    db.user.create_index("verification_token")
    db.user.create_index("security.password_reset_token")
   
    click.echo("Initialized the database.")


@click.command("init-db")
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")




def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)