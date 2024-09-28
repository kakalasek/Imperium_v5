# This file contains models of tables for this app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Crack_john(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    hash_format = db.Column(db.String(50), nullable=False)
    attack_type = db.Column(db.String(30), nullable=False)
    crack_json = db.Column(db.Text, nullable=False)