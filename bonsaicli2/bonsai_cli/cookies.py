"""
This file contains the class to handle cookies for version 2 of the bonsai command line
"""
__author__ = "Lisa Peters"
__copyright__ = "Copyright 2020, Microsoft Corp."

# pyright:reportPrivateUsage=false

from configparser import RawConfigParser, NoOptionError
from datetime import datetime, timedelta
import os
from os.path import expanduser, join
from typing import Any, Optional
from uuid import UUID, uuid4

from .logger import Logger

_BONSAI_COOKIE_FILE = ".bonsaicookies"
_USERID_SECTION = "USER"
_SESSION_ID_SECION = "SESSION"
_APPLICATION_INSIGHTS_SECTION = "APPLICATION_INSIGHTS"
_COOKIE_SECTIONS = [_USERID_SECTION, _SESSION_ID_SECION, _APPLICATION_INSIGHTS_SECTION]
_SESSION_ID_SPLIT_CHAR = "|"
_SESSSION_ID_TIMEDELTA = timedelta(minutes=10)

log = Logger()


class SessionId(object):
    """
    A simple class to hold a session id uuid and expiry value.
    """

    def __init__(self, value: UUID, expiry: Optional[datetime] = None):
        self.value = value
        self.expiry = expiry if expiry else self.update_expiry()

    def __str__(self):
        return "{}{}{}".format(self.value, _SESSION_ID_SPLIT_CHAR, self.expiry)

    def expired(self) -> bool:
        return datetime.utcnow() > self.expiry

    def get_value(self) -> str:
        return str(self.value)

    def update_expiry(self) -> datetime:
        self.expiry = datetime.utcnow() + _SESSSION_ID_TIMEDELTA
        return self.expiry


class CookieConfiguration(object):
    """
    Manages cookie values for the user. This includes a unique guid with
    no PII data for the User Id and a Session Id with an expiry.
    """

    def __init__(self):
        self.user_id = None
        self.session_id = SessionId(uuid4())

        self._config_parser = RawConfigParser(allow_no_value=True)
        self._read_config()
        self._parse_config()

        if not self.user_id:
            self.user_id = uuid4()
            self._update_value(section=_USERID_SECTION, user_id=self.user_id)

        if self.session_id.expired():
            self.session_id = SessionId(uuid4())
        else:
            self.session_id.update_expiry()
        self._update_value(section=_SESSION_ID_SECION, session_id=str(self.session_id))

    @property
    def _config_file(self):
        return join(expanduser("~"), _BONSAI_COOKIE_FILE)

    def get_user_id(self) -> str:
        return str(self.user_id)

    def get_session_id(self) -> str:
        return self.session_id.get_value()

    def get_application_insights_value(self, option: str) -> str:
        try:
            return self._config_parser.get(_APPLICATION_INSIGHTS_SECTION, option)
        except NoOptionError:
            return "false"

    def _write_config_to_file(self) -> None:
        try:
            with open(self._config_file, "w") as f:
                self._config_parser.write(f)
        except (FileNotFoundError, PermissionError):
            log.warning("Unable to write to {}".format(self._config_file))

    def _read_config(self) -> None:
        if os.access(self._config_file, os.R_OK):
            self._config_parser.read(self._config_file)
        else:
            self._write_config_to_file()

    def _parse_config(self) -> None:
        for section in _COOKIE_SECTIONS:
            if not self._config_parser.has_section(section):
                self._config_parser.add_section(section)
            else:
                # If this is the session section, cast the values into a SessionId object
                for _, value in self._config_parser.items(section):
                    if section == _SESSION_ID_SECION:
                        session_id_str, expiry_str = value.split(_SESSION_ID_SPLIT_CHAR)
                        session_id: UUID = UUID(session_id_str)
                        expiry: datetime = datetime.strptime(
                            expiry_str, "%Y-%m-%d %H:%M:%S.%f"
                        )
                        self.session_id = SessionId(session_id, expiry)
                    elif section == _USERID_SECTION:
                        self.user_id = UUID(value)

        self._write_config_to_file()

    def _update_value(self, section: str, **kwargs: Any) -> None:
        if not kwargs:
            return

        for key, value in kwargs.items():
            self._config_parser.set(section, key, value)
            self._write_config_to_file()
