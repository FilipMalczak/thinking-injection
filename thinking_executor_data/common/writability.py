from logging import getLogger

from thinking_programming.exceptions import NoneValueException, InvalidStateException
from thinking_programming.readwrite import ReadWrite
from thinking_reflection.discovery import discover

log = getLogger(__name__)

class WritingDisabledException(InvalidStateException):
    def __init__(self, db: str):
        InvalidStateException.__init__(self, f"Attempted writing to database ({db or 'unknown'}) while writing disabled")
        self.db = db

@discover
class WritabilityManager:
    def __init__(self):
        self._access: ReadWrite = ReadWrite.RO
        log.debug("Writing is disabled at startup")

    def current(self) -> ReadWrite:
        return NoneValueException.guard(self._access)

    def can_write(self) -> bool:
        return self._access == ReadWrite.RW

    def allow_writing(self):
        assert self._access == ReadWrite.RO
        log.debug("Writing allowed")
        self._access = ReadWrite.RW

    def disallow_writing(self):
        # initially there was `assert self._access == ReadWrite.RW` here
        # but I think that we should disallow writing at any time - even if already disallowed;
        # the rationale behind it is that RO mode should be the default and the RW mode should be treated as special;
        # along these lines, at any time you should be able to say "disallow writing" to make sure you're in the default
        # mode
        prev_access = self._access
        self._access = ReadWrite.RO
        if prev_access != ReadWrite.RO:
            log.debug("Writing disallowed")

    def require_writing(self, db: str=None):
        """
        :param db: Optional name of the database that is attempting a write operation. Used only for enhancing exeption message.
        """
        if not self.can_write():
            raise WritingDisabledException(db)