from datetime import date, time, datetime
from functools import reduce
from types import GenericAlias

from terminusdb_client import DocumentTemplate, EnumTemplate, TaggedUnion

XSD_TYPES = {
    int: "xsd:integer",
    float: "xsd:decimal",
    str: "xsd:string",
    bool: "xsd:boolean",
    date: "xsd:date",
    time: "xsd:time",
    datetime: "xsd:dateTime"
    #todo timedelta?
}

SCHEMA_CONTAINERS = {
    list: "List",
    set: "Set"
    #todo dict
}



class TerminusEntity(DocumentTemplate):

    # this cannot be a property, because DocumentTemplate does some internal fuckery and won't recognize the type
    # if this was @identifier.setter def identifier(self, val): ...
    # and we did x.identifier = "abc"
    # we'd get a type mismatch, as Terminus lib won't see the property type, will assume it None and will complain
    # that str != NoneType
    def entity_id(self, val: str=None) -> str | None:
        if val is None:
            return self.simplify_id(self._id) if self._id else self._id
        self._id = self.simplify_id(val)

    def document_id(self, val: str=None) -> str | None:
        if val is None:
            return self._id
        self._id = self.simplify_id(val)

    def data_id(self, val: str=None) -> str | None:
        if val is None:
            return "terminusdb:///data/"+self.document_id()
        self._id = self.simplify_id(val)

    @classmethod
    def simplify_id(cls, val: str) -> str:
        """
        Returns the actual ID, as presented in the dashboard.
        Assumes that val is of structure [trash][classname]/[id].
        Trash is usually something like "terminusdb://data/".
        """
        trash, prefix, the_id = val.partition(schema_id(cls)+"/")
        return the_id

    @classmethod
    def schema_dict(cls) -> dict:
        result = schema_stub(cls)
        def describe_type(t):
            if t in XSD_TYPES:
                return XSD_TYPES[t]
            elif t in SCHEMA_CONTAINERS:
                assert False, "Container field types must be parametrized with element type!"
            elif isinstance(t, GenericAlias):
                assert t.__origin__ in SCHEMA_CONTAINERS #todo msg
                assert len(t.__args__) == 1
                elem_t = t.__args__[0]
                assert issubclass(elem_t, TerminusEntityType) or elem_t in XSD_TYPES
                return {
                    "@type": SCHEMA_CONTAINERS[t.__origin__],
                    "@class": schema_id(elem_t)
                }
            elif issubclass(t, TerminusEntityType):
                return schema_id(t)
            else:
                assert False, f"Unsupported field type {t}" #todo msg
            #todo no support for optionals or subdocuments yet
        for name, t in cls.__annotations__.items():
            result[name] = describe_type(t)
        return result

    def __str__(self):
        d = {}
        d["entity_id"] = self.entity_id()
        for k in type(self).__annotations__.keys():
            d[k] = str(getattr(self, k))

        return type(self).__name__+"("+str(d)+")"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.entity_id() != other.entity_id():
            return False
        for k in type(self).__annotations__:
            v = getattr(self, k)
            ov = getattr(other, k)
            if v != ov:
                return False
        return True

    def __hash__(self):
        return id(self)
    #DO NOT IMPLEMENT __hash__ MANUALLY!
    # default of id(self) is correct
    # __eq__ will compare field-by-field, entity_id() included
    # if we read the same DB object to 2 different python objects, they will satisfy ==, but should be hashed as different
    # objects in memory
    # so, if we save a new entity and it gets an ID, the hash stays the same, so dicts, sets, etc won't go bonkers



TerminusEntityType = TerminusEntity | DocumentTemplate | EnumTemplate

TerminusValueType = reduce(lambda x, y: x | y, XSD_TYPES.keys())
"""
Should only be used for typing; to check whether type is a value type do `type in XSD_TYPES`.
"""

TerminusPropertyType = TerminusEntityType | TerminusValueType

def schema_id[T: TerminusPropertyType](t: type[T]) -> str:
    # don't dispatch schema_dict/_to_dict - id will be the same in both cases and we'll avoid infinite loops this way
    if issubclass(t, TerminusEntityType):
        return t._to_dict()["@id"]
    else:
        assert t in XSD_TYPES
        return XSD_TYPES[t]

def to_schema[T: TerminusEntityType](t: type[T]) -> dict:
    #todo the skip_checking arg could be useful; look into how it is used by consumers
    if issubclass(t, TerminusEntity):
        return t.schema_dict()
    return t._to_dict()

def schema_stub[T: TerminusEntityType](t: type[T]) -> dict:
    """
    Stupid-simple schema of class - just the id and key, no properties or relationships. Used when registering schemas
    (we first register stub for every type, then replace them w/ actual schemas, to avoid schema check failures).
    """
    return {
        "@type": "Class",
        "@id": schema_id(t),
        '@key': {'@type': 'Random'}
    }

def known_types():
    bases = set(TerminusEntityType.__args__)
    bases.add(TaggedUnion)
    result = set()
    def gather(t):
        if t not in bases:
            result.add(t)
        for subtype in t.__subclasses__():
            if subtype not in result:
                gather(subtype)
    for b in bases:
        gather(b)
    return result
