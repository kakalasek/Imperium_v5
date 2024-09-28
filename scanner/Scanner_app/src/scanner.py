# This file is the main entrypoint of this app. It contains all the routes #

# Imports #
from flask import request, Flask
from models import db, Scan
import subprocess
import json
import xmltodict
import os
from celery import shared_task
from util import celery_init_app
from sqlalchemy.exc import OperationalError
from errorhandler import handle_error
from exceptions import ParameterException
from sqlalchemy import text





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





# Tasks #
@shared_task()
def add_scan(options: str, range: str, scan_type: str) -> None:
    """
    This task initiates the scan and adds it into the database

    Arguments
    ---------
    options -> Those are the special options for the scan
    range -> These are the adresses or domains to be scanned
    scan_type -> Type of the scan as string

    Returns
    -------
    None

    Exceptions
    ----------
    OperationalError -> Thrown if there is a database malfunction
    """    
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))    # Testing if the database is alive
    
        xml_content = subprocess.getoutput(f"nmap -oX - {options} {range}") # Run the scan and create an XML
        data_dict = xmltodict.parse(xml_content)    # Convert the XML to dict

        json_output = data_dict['nmaprun']
        json_output = json.dumps(json_output)   # Convert the dict to JSON
                
        new_scan = Scan(name=scan_type, target=range, scan_json=json_output)    
        db.session.add(new_scan)
        db.session.commit()
    
    except OperationalError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)





# Routes #
@app.route("/@test")    
def test():
    """
    This is the test route for this app. It checks if this app is alive and working 
    """
    return '', 200

@app.route("/@scan", methods=["POST"])  # This route is used to start the scan
def scan():
    """
    This route checks the parameters and initiates the s 
    """
    try:
        if 'options' not in request.args:
            raise ParameterException("Options parameter is missing from the request")
        
        if 'range' not in request.args:
            raise ParameterException("Range parameter is missing from the request")
        
        if 'scan_type' not in request.args:
            raise ParameterException("Scan type parameter is missing from the request")

        options = request.args.get('options')   # Get the options of the scan
        range = request.args.get('range')   # Get the range of the scan
        scan_type = request.args.get('scan_type')   # Get the scan type

        add_scan.delay(options, range, scan_type)   # Call Celery to execute and add the scan

        return '', 201

    except ParameterException as e:
        handle_error(e)
        return '', 400

    except Exception as e:
        handle_error(e)
        return '', 400


# Main #
if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all() # Creates the tables

        app.run(debug=True, port=3001, host="0.0.0.0") 

    except OperationalError as e:
        handle_error(e)

    except Exception as e:
        handle_error(e)