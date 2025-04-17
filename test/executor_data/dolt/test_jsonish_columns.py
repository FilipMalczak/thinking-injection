from dataclasses import dataclass
from random import Random
from types import GenericAlias
from uuid import uuid4

from sqlalchemy import Column, INT
from thinking_tests.running.start import run_current_module

from test.util import parametrized_case
from thinking_executor.executor import TaskExecutor
from thinking_executor_data.dolt.sqlalchemy.base import JSON, BSON, Pickle, SqlAlchemyEntity
from thinking_executor_data.dolt.sqlalchemy.storage import DoltStorage
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.typeset import from_packages
from thinking_programming.serialization import Serializable, CustomSerializable, SerializableMixin
from thinking_programming.tracing import traced

#todo change seed per run? or maybe run each test twice - with constant seed and with timestamp-based seed?
RANDOM: Random = Random(0xDEADBEEF)

JSON_LIKE_COLUMN_TYPES = [
    JSON,
    BSON,
    Pickle
]

@dataclass
class SimpleSerializable(SerializableMixin):
    txt: str
    i: int

#todo more love for serializable; at least the case where it has list[int] field and another with dict

RANDOMIZERS = {
    int: lambda: RANDOM.randint(0, 1000),
    float: lambda: RANDOM.random(),
    bool: lambda: RANDOM.random() > 0.5,
    str: lambda: str(uuid4()),
    SimpleSerializable: lambda: SimpleSerializable(random_value(str), random_value(int))
}

PRIMITVE_TYPES = [
    int,
    float,
    bool,
    str
]
SIMPLE_TYPES = PRIMITVE_TYPES + [ SimpleSerializable ]

def construct_type_variants(t):
    return [
        t,
        list[t],
        dict[str, t]
        #todo more variants, like list[dict[...]], dict[str, list[...]], etc
    ]

def random_value(t):
    if t in RANDOMIZERS:
        return RANDOMIZERS[t]()
    assert isinstance(t, GenericAlias), f"Actually: {t}"
    container_type = t.__origin__
    assert container_type in [list, dict]
    element_type = t.__args__[0] if container_type == list else t.__args__[1]
    if container_type == list:
        return [ random_value(element_type) for i in range(RANDOM.randint(2, 5)) ]
    else:
        return { random_value(str): random_value(element_type) for i in range(RANDOM.randint(2, 5)) }


def to_class_name(ValueT: type):
    if ValueT in SIMPLE_TYPES:
        return ValueT.__name__
    if ValueT.__origin__ == list:
        return "list_of_"+to_class_name(ValueT.__args__[0])
    return "dict_of_" + to_class_name(ValueT.__args__[1])


def entity_with_column(ColumnT: type, entity_name: str) -> type:
    result = type(
        entity_name,
        (SqlAlchemyEntity, ),
        {
            "id_": Column(INT, primary_key=True, autoincrement=True),
            "data": Column(ColumnT)
        }
    )
    return result

def given_entity_can_store_given_data(EntityType, data_type):
    ctx = ConfigurableContext([
        *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.dolt")
    ])
    with ctx.lifecycle() as idx:
        executor = idx.instance(TaskExecutor)
        repo = idx.instance(DoltStorage).repository(EntityType)

        @executor.stage
        def top_level():
            @executor.step
            def a_step():
                saved = repo.save_one(EntityType(data=random_value(data_type)))
                assert repo.count().all() == 1
                assert [x.id_ for x in repo.find().all()] == [saved.id_]

for JsonLikeT in JSON_LIKE_COLUMN_TYPES:
    RawEntityType = entity_with_column(JsonLikeT, "Entity_with_" + JsonLikeT.__name__)
    for SimpleT in SIMPLE_TYPES:
        for VariantT in construct_type_variants(SimpleT):
            SpecializedEntityType = entity_with_column(
                JsonLikeT[VariantT],
                "Entity_with_" + JsonLikeT.__name__ + "_over_" + to_class_name(VariantT)
            )

            if SimpleT in PRIMITVE_TYPES:
                @parametrized_case(params=(RawEntityType, VariantT))
                def raw_json_like_works_with_any_primitive_type_variant(raw_type, variant):
                    given_entity_can_store_given_data(raw_type, variant)

            @parametrized_case(params=(SpecializedEntityType, VariantT))
            def specialized_json_like_works_with_matching_variant(specialized_type, variant):
                given_entity_can_store_given_data(specialized_type, variant)


if __name__=="__main__":
    run_current_module()