from typing import Any

def _quote_str(x) -> str:
    if isinstance(x, str):
        return "'"+x+"'"
    return str(x)

class StrReprMixin:
    def _str_properties(self) -> list[str]:
        #todo this can be figured out based on annotations (they prpb
        return []

    def _vars(self) -> dict[str, Any]:
        try:
            return dict(vars(self))
        except:
            try:
                return self._asdict()
            except:
                assert False, "Doesn't support vars() nor _asdict()! Override _vars() manually!"

    def _tweak_repr_properties(self, props: dict[str, Any]) -> dict[str, Any]:
        return props

    def __str__(self):
        return f"{type(self).__name__}({', '.join(k+'='+_quote_str(getattr(self, k)) for k in self._str_properties())})"

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(k+'='+_quote_str(v) for k, v in self._tweak_repr_properties(self._vars()).items())})"
