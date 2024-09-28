# This file contains all the custom exceptions #

class ParameterException(Exception):
    def __init__(self, message):
        super().__init__(message)