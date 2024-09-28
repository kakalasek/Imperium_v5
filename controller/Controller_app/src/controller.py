# This file is the main entrypoint of this app. It contains all the routes #

# Imports #
from flask import Flask, render_template, url_for, redirect, request
from forms import ScanForm, JohnForm
from models import db, Scan, Crack_john
from flask_config import ApplicationConfig
from config import read_config
import json
import requests
from errorhandler import handle_error
from sqlalchemy.exc import OperationalError
from exceptions import RequestError, EndpointNotSet
from requests.exceptions import ConnectionError
from sqlalchemy import text





# Configuration #
app = Flask(__name__)   
app.config.from_object(ApplicationConfig)
db.init_app(app)   

config_data = read_config() 





# Global variables #
scans = [] 
cracks_john = []
endpoints = {   
    'scanner': config_data['scanner_endpoint'],
    'password_cracker': config_data['password_cracker_endpoint']
} 





# Special functions #
def get_scans() -> None:   
    """
    This function retrieves all the scans from the database and puts them into the "scans" list

    Arguments
    ---------
    None

    Returns
    -------
    None

    Exceptions
    ---------- 
    OperationalError -> Thrown if the database is not working
    """
    global scans
    scans = []  # Sets scans to an empty array, so the scans wont be added there twice

    for scan in Scan.query.all():   
            scans.append({
                'id': scan.id,
                'name': scan.name,
                'target': scan.target,
                'scan_json': scan.scan_json
            })

def get_cracks_john() -> None:
    """
    This function retrieves all the john cracks from the database and puts them into the "cracks_john" list

    Arguments
    ---------
    None

    Returns
    -------
    None

    Exceptions
    ---------- 
    OperationalError -> Thrown if the database is not working
    """
    global cracks_john
    cracks_john = []    # Sets scans to an empty array, so the scans wont be added there twice


    for crack_john in Crack_john.query.all():
        cracks_john.append({
            'id': crack_john.id,
            'filename': crack_john.filename,
            'hash_format': crack_john.hash_format,
            'attack_type': crack_john.attack_type,
            'crack_json': crack_john.crack_json
        })





# Routes #

    # Special Routes #
@app.errorhandler(404)
def not_found(e):
    """
    This is a special error handler for the 404 error
    """
    return render_template('err.html', message='Page Not Found'), 404

@app.route("/")
@app.route("/home")
def home():
    """
    This is the default home route 
    """
    try:
        return render_template('home.html'), 200
    except Exception as e:
        r = handle_error(e)
        return r



    # Scanner #
@app.route("/scanner", methods=['GET', 'POST']) 
def scanner():
    """
    This is the default scanner route. It contains the scan form and a list of all initiated scans

    Exceptions
    ----------
    ConnectionError (EndpointNotSet) -> Thrown if the endpoint does not respond

    OperationalError -> Thrown if updating the 'scans' array fails because of a database malfunction
    """
    try:
        endpoint_test = requests.get(f"{endpoints['scanner']}/@test")    # Check if the scanner node is alive

        # Checking the returned status code, just to be sure
        if endpoint_test.status_code == 200:
            scanform = ScanForm()

            get_scans() 

            if request.method == 'POST' and scanform.validate():    
                options = scanform.scan_type.data   
                scan_name = 'Scan'
                scan_range = scanform.ip.data 

                match options: 
                    case '-sS':
                        scan_name = 'SYN Scan'
                    case '-sV':
                        scan_name = 'Version Scan'
                    case '-O':
                        scan_name = 'System Scan'
                    case '-sF':
                        scan_name = 'Fin Scan'
                    case '-sU':
                        scan_name = 'UDP Scan'
                    case '-sT':
                        scan_name = 'Connect Scan'

                if scanform.no_ping.data:   
                    options += " -Pn"
                if scanform.randomize_hosts.data:
                    options += " --randomize-hosts"
                if scanform.fragment_packets.data:
                    options += " -f"

                requests.post(f"{endpoints["scanner"]}/@scan?range={scan_range}&options={options}&scan_type={scan_name}")
                return redirect(url_for("scanner"))

            return render_template('scanner.html', scanform=scanform, scans=scans), 200
        else:
            raise ConnectionError
        
    except ConnectionError as e:    
        try:
            raise EndpointNotSet("Endpoint Not Set")  # Just to have that "Endpoint Not Set" in the message
        except Exception as e:
            r = handle_error(e)   
            return r, 400

    except OperationalError as e:
        r = handle_error(e)
        return r, 500

    except Exception as e:  
        r = handle_error(e)
        return r, 500

@app.route("/scanner/scan") 
def scan():
    """
    This is the scan route. It contains the list of all found hosts in a particular scan

    Exceptions
    ----------
    ConnectionError (EndpointNotSet) -> Thrown if the endpoint does not respond

    OperationalError -> Thrown if updating the 'scans' array fails because of a database malfunction

    RequestError -> Thrown if there is a problem with the request, e. g. invalid parameters
    """
    try:
        endpoint_test = requests.get(f"{endpoints['scanner']}/@test")    # Check if the scanner node is alive

        if endpoint_test.status_code == 200:
            get_scans() 

            global scans
            scan_id = request.args.get('scan_id')
            scan_json = {}  # JSON for this particular scan will be stored here

            if scan_id == None: 
                raise RequestError("Invalid Scan ID")

            for scan in scans: # Check for each entry in the scans table. If the scan is found, load it into 'scan_json' and break
                if scan["id"] == int(scan_id):
                    scan_json = json.loads(scan["scan_json"])
                    break
            
            if not scan_json:   
                raise RequestError("Invalid Scan ID")
            
            return render_template('scan.html', scan_json=scan_json, scan_id=scan_id), 200
        else:
            raise ConnectionError

    except ConnectionError as e:    
        try:
            raise EndpointNotSet("Endpoint Not Set")   # Just to have that "Endpoint Not Set" in the message
        except Exception as e:
            r = handle_error(e)   
            return r, 400

    except RequestError as e:
        r = handle_error(e)
        return r, 400

    except OperationalError as e:
        r = handle_error(e)
        return r, 500

    except Exception as e:
        r = handle_error(e)
        return r, 500

@app.route("/scanner/host")
def host():
    """
    This is the host route. It contains all the information about a particular host in a particular scan

    Exceptions
    ----------
    ConnectionError (EndpointNotSet) -> Thrown if the endpoint does not respond

    OperationalError -> Thrown if updating the 'scans' array fails because of a database malfunction

    RequestError -> Thrown if there is a problem with the request, e. g. invalid parameters
    """
    try:
        endpoint_test = requests.get(f"{endpoints['scanner']}/@test")    # Check if the scanner node is alive

        if endpoint_test.status_code == 200:

            global scans
            without_mac = True  # Is here because the json looks differently depending on if the scan was able to determine the MAC address or not
            scan_id = int(request.args.get('scan_id'))
            host_ip = request.args.get('host_ip')
            host_json = {}

            get_scans()

            if scan_id == None: 
                raise RequestError("Invalid Scan ID")
            
            if host_ip == None: 
                raise RequestError("Invalid Host IP")
            
            for scan in scans:
                if scan["id"] == scan_id:
                    scan_json = json.loads(scan["scan_json"])

                    if isinstance(scan_json['host'], dict): # If scan_json['host'] is a dictionary a single host was scanned, so there is no need for further ip control

                        if "@addr" in scan_json['host']['address']: 
                            host_json = scan_json['host']
                        else:
                            host_json = scan_json['host']
                            without_mac = False

                    else:   # Multiple hosts were scanned, so the right one must be found
                        for host in scan_json['host']:

                            if "@addr" in host['address'] and host['address']['@addr'] == host_ip:
                                host_json = host

                            elif host['address'][0]['@addr'] == host_ip:
                                host_json = host
                                without_mac = False
                    break

            if not host_json:   
                raise RequestError("Invalid Scan ID or Host IP")

            return render_template('host.html', data=host_json, without_mac=without_mac, scan_id =scan_id, host_ip=host_ip), 200
        else:
            raise ConnectionError

    except ConnectionError as e:  
        try:
            raise EndpointNotSet("Endpoint Not Set") 
        except Exception as e:
            r = handle_error(e)   
            return r, 400

    except RequestError as e:
        r = handle_error(e)
        return r, 400

    except OperationalError as e:
        r = handle_error(e)
        return r, 500

    except Exception as e:
        r = handle_error(e)
        return r, 500

@app.route("/scanner/scan/show_json") 
def show_json():
    """
    This the scanner show JSON route. It simply renders the whole json for a particular scan or host

    Exceptions
    ----------
    ConnectionError (EndpointNotSet) -> Thrown if the endpoint does not respond

    RequestError -> Thrown if there is a problem with the request, e. g. invalid parameters
    """
    try:
        endpoint_test = requests.get(f"{endpoints['scanner']}/@test")    # Check if the scanner node is alive

        if endpoint_test.status_code == 200:
            global scans
            scan_id = int(request.args.get('scan_id'))
            host_json = {}
            scan_json = {}

            if scan_id == None: 
                raise RequestError("Invalid Scan ID")

            if request.args.get('host_ip'): # For JSON of a host
                host_ip = request.args.get('host_ip')

                for scan in scans: 
                    if scan["id"] == scan_id: 
                        scan_json = json.loads(scan["scan_json"])

                        if isinstance(scan_json['host'], dict): # If scan_json['host'] is a dictionary a single host was scanned, so there is no need for further ip control
                            if "@addr" in scan_json['host']['address']: 
                                host_json = scan_json['host']
                                return host_json, 200

                            else:
                                host_json = scan_json['host']
                                return host_json, 200

                        else:   # Multiple hosts were scanned, so the right one must be found
                            for host in scan_json['host']: 
                                if "@addr" in host['address']:  
                                    if host['address']['@addr'] == host_ip:
                                        host_json = host
                                        return host_json, 200

                                elif host['address'][0]['@addr'] == host_ip:
                                    host_json = host
                                    return host_json, 200

                        break

                if not host_json:  
                    raise RequestError("Invalid Scan ID or Host IP")
                    
            else:   # For JSON of a scan
                for scan in scans: 
                    if scan["id"] == scan_id:
                        scan_json = json.loads(scan["scan_json"])
                        return scan_json, 200
                    
                if not scan_json:  
                    raise RequestError("Invalid Scan ID")
        else:
            raise ConnectionError 
    
    except ConnectionError as e: 
        try:
            raise EndpointNotSet("Endpoint Not Set")   
        except Exception as e:
            r = handle_error(e)   
            return r, 400

    except RequestError as e:
        r = handle_error(e)
        return r, 400

    except Exception as e:
        r = handle_error(e)
        return r, 500



    # Password Cracker #
@app.route("/password_cracker")
def password_cracker():
    """
    This is the default password cracker route. It contains a little navigation between the different utilities of the password cracker

    Exceptions
    ----------
    ConnectionError (EndpointNotSet) -> Thrown if the endpoint does not respond
    """
    try:
        endpoint_test = requests.get(f"{endpoints['password_cracker']}/@test")  # Check if the scanner node is alive

        if endpoint_test.status_code == 200:
            return render_template('password_cracker.html'), 200
        
        else:
            raise ConnectionError

    except ConnectionError as e: 
        try:
            raise EndpointNotSet("Endpoint Not Set") 
        except Exception as e:
            r = handle_error(e)   
            return r, 400

    except Exception as e:
        r = handle_error(e)
        return r, 500

@app.route("/password_cracker/john", methods=['GET', 'POST'])
def john():
    """
    This is the password cracker John route. It contains the John form and a list of all attempted password crackings

    Exceptions
    ----------
    ConnectionError (EndpointNotSet) -> Thrown if the endpoint does not respond

    OperationalError -> Thrown if updating the 'cracks_john' array fails because of a database malfunction
    """
    try:
        endpoint_test = requests.get(f"{endpoints['password_cracker']}/@test")  # Check if the password cracker node is alive

        if endpoint_test.status_code == 200:
            johnform = JohnForm()
            global cracks_john

            get_cracks_john()

            if request.method == 'POST' and johnform.validate():
                file = johnform.file.data
                format = johnform.format.data
                attack_type = johnform.attack_type.data
                dictionary = johnform.dictionary.data

                requests.post(url=f"{endpoints["password_cracker"]}/@crack_john?filename={file.filename}&format={format}&attack_type={attack_type}", 
                            files={"file": file, "dictionary": dictionary})

                return redirect(url_for('john'))

            return render_template('john.html', johnform=johnform, cracks_john=cracks_john), 200
        
        else:
            raise ConnectionError

    except ConnectionError as e:    
        try:
            raise EndpointNotSet(f"Endpoint Not Set")  
        except Exception as e:
            r = handle_error(e)   
            return r, 400
    
    except OperationalError as e:
        r = handle_error(e)
        return r, 500 

    except Exception as e:
        r = handle_error(e)
        return r, 500

@app.route("/password_cracker/crack_john")
def crack_john():
    """
    This is the crack John route. It contains all information about a specific password cracking attempt

    Exception
    ---------
    ConnectionError (EndpointNotSet) -> Thrown if the endpoint does not respond

    OperationalError -> Thrown if updating the 'cracks_john' array fails because of a database malfunction

    RequestError -> Thrown if there is a problem with the request, e. g. invalid parameters
    """
    try:
        endopoint_test = requests.get(f"{endpoints['password_cracker']}/@test")    # Check if the password cracker node is alive

        if endopoint_test.status_code == 200:
            global cracks_john 
            crack_john_id = int(request.args.get('crack_john_id'))
            crack_john_json = {}

            get_cracks_john()

            if crack_john_id == None: 
                raise RequestError("Invalid Crack ID")
            
            for crack_john in cracks_john:
                if crack_john['id'] == crack_john_id:
                    crack_john_json = json.loads(crack_john['crack_json'])

            if not crack_john_json:   
                raise RequestError("Invalid Crack ID")

            return render_template('john_crack.html', cracks_john=crack_john_json), 200
        
        else:
            raise ConnectionError

    except ConnectionError as e:    
        try:
            raise EndpointNotSet(f"Endpoint Not Set")  
        except Exception as e:
            r = handle_error(e)   
            return r, 400

    except RequestError as e:
        r = handle_error(e)
        return r, 400
    
    except OperationalError as e:
        r = handle_error(e)
        return r, 500

    except Exception as e:
        r = handle_error(e)
        return r, 500





# Main #
if __name__ == '__main__':
    """
    This is the main entrypoint of the program 
    """
    try:
        # Checking if the database is working    
        with app.app_context():
            db.session.execute(text("SELECT 1"))

        # Starting the app
        app.run(host="0.0.0.0", port=5000, debug=True)

    except OperationalError as e:
        with app.app_context():
            r = handle_error(e)

    except Exception as e:
        with app.app_context():
            r = handle_error(e)