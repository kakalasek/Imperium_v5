# This file contains all the models of all the tables used in this app #

# Imports #
from flask_sqlalchemy import SQLAlchemy





# Configuration #
db = SQLAlchemy()





# Models #
class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    target = db.Column(db.String(100), nullable=False)
    scan_json = db.Column(db.Text, nullable=False)