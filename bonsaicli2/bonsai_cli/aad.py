"""
This file contains the main code for AAD authentication in  version 2 of the bonsai command line
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

import os
import sys
from typing import Dict, Optional

from .logger import Logger
from .exceptions import AuthenticationError

from msal import PublicClientApplication
from msal_extensions import TokenCache
from requests.exceptions import ConnectionError

log = Logger()

# Documentation on AAD configuration:
# https://docs.microsoft.com/bs-latn-ba/azure/active-directory/develop/msal-client-application-configuration

_AAD_CLIENT_ID = "2e0d2c17-604c-4986-b574-ac7fb93b9897"

_AAD_SCOPE = ["https://preview.bons.ai/.default"]


_MICROSOFT_BONSAI_CACHE = ".microsoftbonsaicache"


def use_password_auth() -> bool:
    return "BONSAI_AAD_USER" in os.environ and "BONSAI_AAD_PASSWORD" in os.environ


def get_aad_cache_file():
    # cache file should be written to home directory
    home = os.path.expanduser("~")
    if home:
        cache_file = os.path.join(home, _MICROSOFT_BONSAI_CACHE)
    else:
        raise RuntimeError("Unable to find home directory.")

    return cache_file


class AADClient(object):
    """
    This object uses the Microsoft Authentication Library for Python (MSAL)
    to log in and authenticate users using AAD.

    The only public method is get_access_token(), which returns an access token
    if one already exists in the cache, else it will fill the cache by
    prompting the user to log in.
    """

    def __init__(self, tenant_id: Optional[str] = None):
        self._cache_file = get_aad_cache_file()

        self.cache = TokenCache(self._cache_file)

        retry_count = 1

        effective_tenant_id = (
            tenant_id
            if tenant_id is not None and tenant_id != "None"
            else "organizations"
        )

        _AAD_AUTHORITY = "https://login.microsoftonline.com/" + effective_tenant_id

        while True:
            try:
                self._app = PublicClientApplication(
                    _AAD_CLIENT_ID, authority=_AAD_AUTHORITY, token_cache=self.cache
                )
                if self._app:
                    break
            except ConnectionError as e:
                log.info(
                    "ConnectionError on attempt {} to "
                    "create msal PublicClientApplication, "
                    "retrying...".format(retry_count)
                )
                if retry_count >= 5:
                    raise e
            retry_count += 1

    def _log_in_with_device_code(self) -> Dict[str, str]:
        """Recommended login method. The user must open a browser to
        https://microsoft.com/devicelogin and enter a unique device code to
        begin authentication."""
        flow = self._app.initiate_device_flow(_AAD_SCOPE)
        print(flow["message"])
        sys.stdout.flush()  # needed to print on Windows
        return self._app.acquire_token_by_device_flow(flow)

    def _log_in_with_password(self) -> Dict[str, str]:
        """This login method is less secure and should be used for
        automation only."""
        return self._app.acquire_token_by_username_password(
            os.environ["BONSAI_AAD_USER"], os.environ["BONSAI_AAD_PASSWORD"], _AAD_SCOPE
        )

    def _get_access_token_from_cache(self):
        """ This also does a token refresh if the access token has expired. """
        result = None
        accounts = self._app.get_accounts()
        if accounts:
            """Bonsai config only gives us the short username, and token cache
            stores accounts by email address (e.g. soc-auto vs
            soc-auto@microsoft.com). So, if there are multiple accounts, assume
            the first one for now."""
            chosen = accounts[0]
            result = self._app.acquire_token_silent(_AAD_SCOPE, account=chosen)
        return result

    def get_access_token(self):

        # attempt to get token from cache
        token = self._get_access_token_from_cache()
        if token:
            return "Bearer {}".format(token["access_token"])

        # no token found in cache, user must sign in and try again
        if use_password_auth():
            self._log_in_with_password()
        else:
            print("No access token found in cache, please sign in.")
            self._log_in_with_device_code()
        token = self._get_access_token_from_cache()
        if token:
            return "Bearer {}".format(token["access_token"])

        message = "Error: could not fetch AAD access token after login."
        raise AuthenticationError(message)
