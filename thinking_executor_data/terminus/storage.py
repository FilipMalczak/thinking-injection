from dataclasses import dataclass
from logging import getLogger
from typing import Iterable

from terminusdb_client import Client, GraphType, WOQLQuery

from thinking_executor_data.common.storage import Storage, RepositoryMetadata, Repository, Find, Count, Exist, ExistByIds, \
    Delete
from thinking_executor_data.terminus.base import TerminusEntityType, TerminusEntity, schema_id, known_types, to_schema, \
    schema_stub
from thinking_executor_data.terminus.client import TerminusClientLifecycle
from thinking_executor_data.terminus.graphql.endpoint import TerminusDbGraphQLEndpoint
from thinking_executor_data.terminus.graphql.query import graphql_entity_query, graphql_id_query
from thinking_executor_data.terminus.graphql.results import deserialize_result_response
from thinking_executor_data.terminus.versioning import TerminusDbVersioning
from thinking_executor_data.common.writability import WritabilityManager
from thinking_injection.injectable import Injectable

from thinking_programming.collectable import Collectable, collect

GraphQLFilter = dict #todo buff it up

log = getLogger(__name__)

@dataclass
class IdHolder:
    _id: str

#todo dedicated exceptions
#IDs are supposed to be entity_ids #todo put it in proper docstring; maybe loosen than restriction by pushing each id through self.entity_type.simplify_id?
@dataclass
class TerminusDbRepository[E: TerminusEntity](Repository[E, str, GraphQLFilter]):
    entity_type: type[E]
    terminus_client: Client
    versioning: TerminusDbVersioning
    gql: TerminusDbGraphQLEndpoint
    writability: WritabilityManager

    def metadata(self) -> RepositoryMetadata[type[E], str, GraphQLFilter]:
        return RepositoryMetadata(TerminusEntityType, str, GraphQLFilter)

    def save(self, *entities: Collectable[E]) -> list[E]:
        es = list(collect(self.entity_type, *entities))
        log.debug(f"Saving {es}")
        self.writability.require_writing("terminusdb")
        out = []
        for c in es:
            id = self.terminus_client.replace_document(
                c,
                GraphType.INSTANCE,
                commit_msg=str(self.versioning.current_coordinates()),
                create=True
            )[0]
            log.debug(f"Saved {c} and obtained id {id}")
            c.entity_id(id)
            out.append(c)
        log.debug(f"Saved {len(out)} entities")
        return out

    def find(self) -> Find[str, GraphQLFilter, E]:
        class TerminusFind(Find[str, GraphQLFilter, E]):
            def by_id(find, _id: str) -> E | None:
                response = self.gql.request(
                    graphql_entity_query(
                        self.entity_type,
                        {"id": "terminusdb:///data/"+schema_id(self.entity_type)+"/"+_id}
                    )
                )
                entities = deserialize_result_response(response, self.entity_type)
                assert len(entities) < 2
                return entities[0] if entities else None

            def by_ids(find, *ids: Collectable[str]) -> Iterable[E]:
                response = self.gql.request(
                    graphql_entity_query(
                        self.entity_type,
                        {"ids": [
                            "terminusdb:///data/" + schema_id(self.entity_type) + "/" + _id
                            for _id in collect(str, *ids)
                        ]}
                    )
                )
                entities = deserialize_result_response(response, self.entity_type)
                return entities

            def where(find, query: GraphQLFilter) -> Iterable[E]:
                gql = graphql_entity_query(
                        self.entity_type,
                        {"filter": query}
                    )
                response = self.gql.request(gql)
                entities = deserialize_result_response(response, self.entity_type)
                return entities

            def all(find) -> Iterable[E]:
                response = self.gql.request(
                    graphql_entity_query(
                        self.entity_type
                    )
                )
                entities = deserialize_result_response(response, self.entity_type)
                return entities
        return TerminusFind()

    def count(self) -> Count[str, GraphQLFilter]:
        class TerminusCount(Count[str, GraphQLFilter]):
            def by_ids(count, *ids: Collectable[str]) -> int:
                q = WOQLQuery().count(
                    "v:cnt",
                    WOQLQuery().woql_and(
                        WOQLQuery().triple("v:Subject", "rdf:type", "@schema:"+schema_id(self.entity_type)),
                        WOQLQuery().woql_or(
                            *[
                                WOQLQuery().eq(
                                    "v:Subject",
                                    "terminusdb:///data/"+schema_id(self.entity_type)+"/"+_id
                                )
                                for _id in collect(str, *ids)
                            ]
                        )
                    )
                )
                result = self.terminus_client.query(q)
                cnt = int(result["bindings"][0]["cnt"]["@value"])
                return cnt

            def where(count, query: GraphQLFilter) -> int:
                response = self.gql.request(
                    graphql_id_query(
                        self.entity_type,
                        {"filter": query}
                    )
                )
                #todo repetitive pattern, extract a function for this
                entities = [ x._id for x in deserialize_result_response(response, IdHolder, self.entity_type) ]
                return len(entities)

            def all(count) -> int:
                q = WOQLQuery().count(
                    "v:cnt",
                    WOQLQuery().triple("v:Subject", "rdf:type", "@schema:" + schema_id(self.entity_type)),
                )
                result = self.terminus_client.query(q)
                cnt = int(result["bindings"][0]["cnt"]["@value"])
                return cnt
        return TerminusCount()

    def exist(self) -> Exist[str, GraphQLFilter]:
        class TerminusExistByIds(ExistByIds):
            def __init__(byids, ids: list[str]):
                byids.ids = ids

            def all(byids) -> bool:
                response = self.gql.request(
                    graphql_id_query(
                        self.entity_type,
                        {
                            "ids": [
                                "terminusdb:///data/" + schema_id(self.entity_type) + "/" + _id
                                for _id in byids.ids
                            ],
                            "limit": 1
                        }
                    )
                )
                entities = [ x._id for x in deserialize_result_response(response, IdHolder, self.entity_type) ]
                return len(entities) == len(byids.ids)

            def any(byids) -> bool:
                response = self.gql.request(
                    graphql_id_query(
                        self.entity_type,
                        {
                            "ids": [
                                "terminusdb:///data/" + schema_id(self.entity_type) + "/" + _id
                                for _id in byids.ids
                            ],
                            "limit": 1
                        }
                    )
                )
                entities = [ x._id for x in deserialize_result_response(response, IdHolder, self.entity_type) ]
                return bool(entities)

        class TerminusExist(Exist[str, GraphQLFilter]):
            def by_id(exist, _id: str) -> bool:
                response = self.gql.request(
                    graphql_id_query(
                        self.entity_type,
                        {"id": "terminusdb:///data/"+schema_id(self.entity_type)+"/"+_id, "limit": 1}
                    )
                )
                entities = [ x._id for x in deserialize_result_response(response, IdHolder, self.entity_type) ]
                return bool(entities)

            def by_ids(exist, *ids: Collectable[str]) -> TerminusExistByIds:
                return TerminusExistByIds(list(collect(str, *ids)))

            def where(exist, query: GraphQLFilter) -> bool:
                response = self.gql.request(
                    graphql_id_query(
                        self.entity_type,
                        {"filter": query, "limit": 1}
                    )
                )
                entities = [ x._id for x in deserialize_result_response(response, IdHolder, self.entity_type) ]
                return bool(entities)
        return TerminusExist()

    def delete(self) -> Delete[str, GraphQLFilter]:
        #even though some methods delegate to each other, don't skip require_writing(), so that if it fails,
        # the stacktrace points to the culprit, not to the delegate
        class TerminusDelete(Delete[str, GraphQLFilter]):
            def by_id(delete, _id: str):
                self.writability.require_writing("terminusdb")
                delete.by_ids(_id)

            def by_ids(delete, *ids: Collectable[str]):
                self.writability.require_writing("terminusdb")
                self.terminus_client.delete_document(
                    [
                        "terminusdb:///data/"+schema_id(self.entity_type)+"/"+_id
                        for _id in collect(str, *ids)
                    ]
                )

            def where(delete, query: GraphQLFilter):
                self.writability.require_writing("terminusdb")
                response = self.gql.request(
                    graphql_id_query(
                        self.entity_type,
                        {"filter": query}
                    )
                )
                ids = [self.entity_type.simplify_id(x._id) for x in deserialize_result_response(response, IdHolder, self.entity_type)]
                delete.by_ids(ids)

            def all(delete):
                self.writability.require_writing("terminusdb")
                delete.where({})
        return TerminusDelete()

class TerminusDbStorage(Injectable, Storage):
    def __init__(self):
        self.terminus_client: Client = None
        self.versioning: TerminusDbVersioning = None
        self.gql: TerminusDbGraphQLEndpoint = None
        self.writability: WritabilityManager = None

    def inject_requirements(self, terminus_lifecycle: TerminusClientLifecycle, versioning: TerminusDbVersioning, gql: TerminusDbGraphQLEndpoint, writability: WritabilityManager) -> None:
        self.terminus_client = terminus_lifecycle.client
        self.versioning = versioning
        self.gql = gql
        self.writability = writability

    def initialize(self):
        log.debug("Registering schema stubs for missing types")
        missing_types = []
        for t in known_types():
            if not self.terminus_client.has_doc(schema_id(t), GraphType.SCHEMA):
                log.debug("Registering schema stub for "+schema_id(t))
                self.terminus_client.replace_document(schema_stub(t), GraphType.SCHEMA, create=True)
                missing_types.append(t)
            else:
                log.debug("Schema "+schema_id(t)+" already exists")
        log.debug("Replacing stubs with actual schemas")
        for t in missing_types:
            log.debug("Registering real schema for "+schema_id(t))
            self.terminus_client.replace_document(to_schema(t), GraphType.SCHEMA, create=True)

    def supports_entity[E](self, t: type[E]) -> bool:
        return issubclass(t, TerminusEntityType)

    def repository[E, ID, Q](self, t: type[E]) -> Repository[E, ID, Q]:
        return TerminusDbRepository(t, self.terminus_client, self.versioning, self.gql, self.writability)