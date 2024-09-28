# This file contains a simple error handler for all possible errors #

# Imports #
import logging





# Configuration #
log_format = '%(asctime)s - %(message)s'
logging.basicConfig(format=log_format)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)





# Functions #
def handle_error(e) -> None:
    """
    This function simply logs the error

    Arguments
    ---------
    e -> Exception to be handled
    """
    log.error(e)