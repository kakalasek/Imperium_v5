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

# App config #
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

# Functions

def create_json_john(john_output: str) -> str:
    john_output = john_output.split(' ')

    n = 0

    cracked_passwords = []
    while not john_output[n].isnumeric():
        cracked_passwords.append({"username": john_output[n].split(':')[0], "password": john_output[n].split(':')[1]})
        n = n + 1

    return json.dumps(cracked_passwords)

# Tasks #

@shared_task()
def add_crack_john(file_content: str, filename: str, format: str, attack_type: str, dictionary_content: str) -> None:
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))

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
    return '', 200

@app.route('/@crack_john', methods=['POST'])
def crack_john():
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

# App starts #
if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all() # Create the tables

        app.run(debug=True, port=3002, host="0.0.0.0") # Start the application
        
    except OperationalError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)