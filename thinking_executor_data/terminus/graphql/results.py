from logging import getLogger
from types import GenericAlias

from thinking_executor_data.terminus.base import SCHEMA_CONTAINERS, TerminusEntity
from thinking_executor_data.terminus.graphql.deser import DESER

log = getLogger(__name__)

def deserialize_result_response[T](data: dict, returned: type[T], container: type=None) -> list[T]:
    if container is None:
        container = returned
    assert isinstance(data, dict)
    assert len(data) == 1
    assert "data" in data and data["data"] is not None, f"Malformed response: {data}"
    assert len(data["data"]) == 1
    assert container.__name__ in data["data"], f"Actual response:\n{data}"
    return deserialize_result_data(list[returned], data["data"][container.__name__])

def deserialize_result_data[T](t: type[T], data: dict | list[dict] | str) -> T:
    if t in SCHEMA_CONTAINERS:
        assert False
    elif isinstance(t, GenericAlias):
        assert t.__origin__ in SCHEMA_CONTAINERS #todo
        assert len(t.__args__) == 1
        assert isinstance(data, list)
        elem_type = t.__args__[0]
        return t.__origin__(deserialize_result_data(elem_type, x) for x in data)
    elif t in DESER:
        # assert isinstance(data, str), f"Data is {data} (type: {type(data)})"
        return DESER[t].deserialize(data)
    elif issubclass(t, TerminusEntity): #todo what about DocumentTemplate and friends?
        assert isinstance(data, dict)
        init_args = {}
        identifier = data["_id"]
        for k, v in data.items():
            if k != "_id":
                #todo assert k in annotations?
                field_type = t.__annotations__[k]
                try:
                    init_args[k] = deserialize_result_data(field_type, v)
                except:
                    raise
        result = t(**init_args)
        result.entity_id(identifier)
        return result
    else:
        #todo should be merged w/ previous elif
        assert isinstance(data, dict)
        init_args = {}
        for k, v in data.items():
            # todo assert k in annotations?
            field_type = t.__annotations__[k]
            init_args[k] = deserialize_result_data(field_type, v)
        result = t(**init_args)
        return result