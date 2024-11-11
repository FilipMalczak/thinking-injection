from inspect import getsourcelines, getsourcefile, isbuiltin
from typing import NamedTuple, Self, Optional


class SourceScope(NamedTuple):
    filename: str
    first_line_no: int
    line_count: int

    @property
    def last_line_no(self) -> int:
        return self.first_line_no + self.line_count - 1

    def __contains__(self, item: Self | 'DescriptorSourceScope') -> bool:
        if item is None:
            return False
        if isinstance(item, DescriptorSourceScope):
            return any(x in self for x in item)
        if item.filename != self.filename:
            return False
        # item declared before self
        if item.last_line_no < self.first_line_no:
            return False
        #item declared further down the file that self
        if item.first_line_no > self.last_line_no:
            return False
        return True

class DescriptorSourceScope(NamedTuple):
    declaration: Optional[SourceScope]
    getter: Optional[SourceScope]
    setter: Optional[SourceScope]

def get_source_scope(x) -> SourceScope:
    if isbuiltin(x):
        return None
    t = type(x)
    if t.__module__ == "builtins" and t not in {type, FUNCTION_TYPE}:
        return None
    lines, first = getsourcelines(x)
    return SourceScope(
        getsourcefile(x),
        first,
        len(lines)
    )

FUNCTION_TYPE = type(get_source_scope)
