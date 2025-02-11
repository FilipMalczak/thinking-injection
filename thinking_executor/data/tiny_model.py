from logging import getLogger
from typing import NamedTuple, Protocol

from tinydb.table import Table

from thinking_reflection.interfaces import interface

TinyDBTable = Table

log = getLogger(__name__)

class TinyDBParameters(NamedTuple):
    path: str

@interface
class TinyConfiguration(Protocol):
    def get_tinydb_parameters(self) -> TinyDBParameters: ...
