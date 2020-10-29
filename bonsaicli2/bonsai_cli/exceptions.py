"""
This file contains the code for custom exceptions in  version 2 of the bonsai command line
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

from typing import Any


class BonsaiClientError(Exception):
    """
    Generic wrapper for exceptions originating in client implementations
    """

    def __init__(self, msg: str, e: str):
        super(BonsaiClientError, self).__init__("{}: {}".format(msg, repr(e)))
        self.original_exception = e


class AuthenticationError(BonsaiClientError):
    def __init__(self, e: Any):
        super(AuthenticationError, self).__init__("Error authenticating user", e)


class RetryTimeoutError(Exception):
    pass


class BonsaiServerError(Exception):
    pass


class SimStateError(Exception):
    pass


class UsageError(Exception):
    pass
