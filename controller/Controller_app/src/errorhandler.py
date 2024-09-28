# This file contains a simple error handler for all possible errors #

# Imports #
from flask import render_template
import logging





# Configuration #
log_format = '%(asctime)s - %(message)s'
logging.basicConfig(format=log_format)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)




# Functions #
def handle_error(e):
    """
    This function simply logs and returns the error to be displayed

    Arguments
    ---------
    e -> Exception to be handled

    Returns
    -------
    Page with the exceptions code to be rendered
    """
    log.error(e)
    return render_template('err.html', message=e)