# This file contains all the custom exceptions #

class RequestError(Exception):
    def __init__(self, message):
        super().__init__(message)

class EndpointNotSet(Exception):
    def __init__(self, message):
        super().__init__(message)