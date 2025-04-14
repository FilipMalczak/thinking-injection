from types import GenericAlias

from thinking_executor_data.terminus.base import XSD_TYPES, SCHEMA_CONTAINERS, TerminusEntity, TerminusValueType
from thinking_executor_data.terminus.graphql.deser import DESER


def graphql_query_body(cls: type, *, lvl: int=0) -> str:
    """
    Should return list of subfields of given type, as understood by graphql. lvl indicates indentation level.

    For example, if final GraphQL query will look like:
    | query {
    |  Container(filter: {holders: {allHave: {txt: {eq: "hello"}}}}) {
    |    _id
    |    holders {
    |      txt
    |    }
    |  }
    | }
    Then graphql_query_body(Container, lvl=2) should return
    |    _id
    |    holders {
    |      txt
    |    }
    """
    result = ["_id"]
    for name, t in cls.__annotations__.items():
        if t in XSD_TYPES:
            result.append(name)
        else:
            actual_type = t
            if t in SCHEMA_CONTAINERS:
                assert False, "elements must be typed" #todo
            elif isinstance(t, GenericAlias):
                assert len(t.__args__) == 1 #todo
                actual_type = t.__args__[0]
            if actual_type in XSD_TYPES:
                result.append(name)
            else:
                result.append(name+" {")
                result.extend(graphql_query_body(actual_type, lvl=lvl+1).split("\n")) #fixme join, split, join, split, ...
                result.append("}")
    joined = "\n".join("  "*lvl + x for x in result)
    return joined


def _graphql_args(args: dict | list | TerminusValueType, *, root=True) -> str:
    out = ""
    if isinstance(args, dict):
        if not root:
            out += "{"
        to_join = []
        for k, v in args.items():
            to_join.append( k+": "+_graphql_args(v, root=False) )
        out += ", ".join(to_join)
        if not root:
            out += "}"
    elif isinstance(args, list):
        out = "[" + ", ".join(_graphql_args(x, root=False) for x in args) + "]"
    else:
        out = DESER[type(args)].serialize(args)
    return out

def _indent(txt: str, lvl: int, prefix: str="  ") -> str:
    return "\n".join(
        prefix*lvl+line
        for line in txt.split("\n")
    )

def graphql_entity_query(cls: type, args: dict=None) -> str:
    return graphql_query(cls, _indent(graphql_query_body(cls), 2), args)

def graphql_id_query(cls: type, args: dict=None) -> str:
    return graphql_query(cls, "    _id", args)

def graphql_query(cls: type, body: str, args: dict=None) -> str:
    a = '('+_graphql_args(args)+')' if args else ''
    return ("""
query {
  """+cls.__name__+a+""" {
"""+body+"""
  }
}
""").strip()
