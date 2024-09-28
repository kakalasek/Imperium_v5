# This file is the main entrypoint of this app. It contains all the routes #

# Imports #
import subprocess
from flask import request, Flask
from models import db, Crack_john
import os
from celery import shared_task
from util import celery_init_app
from sqlalchemy.exc import OperationalError
from errorhandler import handle_error
from exceptions import ParameterException
from sqlalchemy import text
import json
from werkzeug.datastructures.file_storage import FileStorage





# Configuration #
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URI']
app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://redis",
        result_backend="redis://redis",
        task_ignore_results=True,
    ),
)

db.init_app(app)
celery_app = celery_init_app(app)





# Special functions #
def create_json_john(john_output: str) -> str:
    """
    This function simply parses the output of john to json and removes unneccesary data from it

    Arguments
    ---------
    john_output -> The output to be parsed

    Returns
    -------
    Json string
    """
    john_output = john_output.split(' ') # The output is in this kind of format (?:hello user:password 2 passwords cracked ...)

    n = 0

    cracked_passwords = []
    while not john_output[n].isnumeric():
        cracked_passwords.append({"username": john_output[n].split(':')[0], "password": john_output[n].split(':')[1]})
        n = n + 1

    return json.dumps(cracked_passwords)





# Tasks #
@shared_task()
def add_crack_john(file_content: str, filename: str, format: str, attack_type: str, dictionary_content: str) -> None:
    """
    This task executes John and saves the output into the database

    Arguments
    ---------
    file_content -> File with hashes
    filename -> Name of the file with hashes
    format -> Format of the hash to be cracked
    attack_type -> Dictionary of brute force
    dictionary_content -> Content of the dictionary file

    Returns
    -------
    None

    Exceptions
    ----------
    IOError -> Thrown if something goes wrong with file operations

    OperationalError -> Thrown if there is a database malfunction
    """
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))    # Testing if the database works

        # The upcoming bash script works with files, so we first need to write correct content into them
        with open("hashes.txt", 'w') as f:
            f.write(file_content)

        if attack_type == 'dictionary':

            with open("dictionary.txt", "w") as f:
                f.write(dictionary_content)

            john_output = subprocess.getoutput(f'./john_crack.sh {format} d')
        else:
            john_output = subprocess.getoutput(f'./john_crack.sh {format}') 

        if john_output:
            crack_json = create_json_john(john_output)
        else:
            crack_json = '{"no_passwords": "true"}'

        new_crack_john = Crack_john(filename=filename, hash_format=format, attack_type=attack_type, crack_json=crack_json)
        db.session.add(new_crack_john)
        db.session.commit()


    except IOError as e:
        handle_error(e)

    except OperationalError as e:
        handle_error(e)

    except Exception as e:
        handle_error(e)





# Routes #
@app.route('/@test')
def test():
    """
    This is the test route for this app. It checks if this app is alive and working 
    """
    return '', 200

@app.route('/@crack_john', methods=['POST'])
def crack_john():
    """
    This is the route to use john for cracking a password. The results of the attempt are saved into the database

    Exceptions
    ----------
    ParemeterException -> Thrown if any of the parameters is either missing or invalid
    """
    try:
        if 'filename' not in request.args:
            raise ParameterException("Filename parameter is missing from the request")
        
        if 'format' not in request.args:
            raise ParameterException("Format parameter is missing from the request")

        if 'attack_type' not in request.args:
            raise ParameterException("Attack type parameter is missing from the request")

        if 'dictionary' not in request.files:
            raise ParameterException("Dictionary parameter is missing from the request")

        if 'file' not in request.files:
            raise ParameterException("File parameter is missing from the request")


        file = request.files['file']
        filename = request.args['filename']
        format =  request.args['format']
        attack_type = request.args['attack_type']
        dictionary = request.files['dictionary']
        
        file_content = file.read().decode('iso8859-15')
        dictionary_content = dictionary.read().decode('iso8859-15')

        add_crack_john.delay(file_content, filename, format, attack_type, dictionary_content)

        return '', 201

    except ParameterException as e:
        handle_error(e)
        return e, 400
    except Exception as e:
        handle_error(e)
        return e, 400





# Main #
if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all() # Creates the tables

        app.run(debug=True, port=3002, host="0.0.0.0")
        
    except OperationalError as e:
        handle_error(e)

    except Exception as e:
        handle_error(e)