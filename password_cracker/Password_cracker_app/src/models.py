# This file contains all the models of all the tables used in this app #

# Imports #
from flask_sqlalchemy import SQLAlchemy





# Configuration #
db = SQLAlchemy()





# Models #
class Crack_john(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    hash_format = db.Column(db.String(50), nullable=False)
    attack_type = db.Column(db.String(30), nullable=False)
    crack_json = db.Column(db.Text, nullable=False)