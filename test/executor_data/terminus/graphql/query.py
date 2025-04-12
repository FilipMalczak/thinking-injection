from typing import Callable

from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.executor_data.terminus.graphql.model import Holder, Container
from thinking_executor_data.terminus.graphql.query import graphql_query_body, graphql_entity_query, graphql_id_query

#todo tests for list/set of primitives

@case
def query_body():
    assert graphql_query_body(Holder) == """
_id
i
txt
""".strip()

    assert graphql_query_body(Container) == """
_id
holders {
  _id
  i
  txt
}
    """.strip()

@case
def entity_query():
    assert graphql_entity_query(Container) == """
query {
  Container {
    _id
    holders {
      _id
      i
      txt
    }
  }
}
    """.strip()

    assert graphql_entity_query(Container, {}) == """
query {
  Container {
    _id
    holders {
      _id
      i
      txt
    }
  }
}
    """.strip()

    assert graphql_entity_query(Container, {"filter": {"holders": {"someHave": {"txt": {"eq": "hello"}}}}}) == """
query {
  Container(filter: {holders: {someHave: {txt: {eq: "hello"}}}}) {
    _id
    holders {
      _id
      i
      txt
    }
  }
}
    """.strip()

    assert graphql_entity_query(Container, {"filter": {"holders": {"someHave": {"txt": {"eq": "hello"}}}}, "limit": 1}) == """
query {
  Container(filter: {holders: {someHave: {txt: {eq: "hello"}}}}, limit: 1) {
    _id
    holders {
      _id
      i
      txt
    }
  }
}
    """.strip()

@case
def id_query():
    assert graphql_id_query(Container) == """
query {
  Container {
    _id
  }
}
    """.strip()

    assert graphql_id_query(Container, {}) == """
query {
  Container {
    _id
  }
}
    """.strip()

    assert graphql_id_query(Container, {"filter": {"holders": {"someHave": {"txt": {"eq": "hello"}}}}}) == """
query {
  Container(filter: {holders: {someHave: {txt: {eq: "hello"}}}}) {
    _id
  }
}
    """.strip()

    assert graphql_id_query(Container, {"filter": {"holders": {"someHave": {"txt": {"eq": "hello"}}}}, "limit": 1}) == """
query {
  Container(filter: {holders: {someHave: {txt: {eq: "hello"}}}}, limit: 1) {
    _id
  }
}
    """.strip()

if __name__=="__main__":
    run_current_module()
    # query_body()