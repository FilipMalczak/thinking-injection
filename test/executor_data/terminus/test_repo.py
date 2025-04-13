from datetime import date, datetime, time
from functools import wraps
from logging import getLogger
from typing import Callable

from thinking_runtime.defaults.recognise_runtime import current_runtime

from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_containers.docker_client import DockerFromEnvClientFactory
from thinking_executor.executor import TaskExecutor
from thinking_executor_data.terminus.base import TerminusEntity
from thinking_executor_data.terminus.graphql.deser import DESER
from thinking_executor_data.terminus.storage import TerminusDbStorage, GraphQLFilter
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.typeset import from_packages

log = getLogger(__name__)


class AllSimpleTypes(TerminusEntity):
    i: int
    f: float
    s: str
    b: bool
    d: date
    dt: datetime
    t: time

def prototype() -> AllSimpleTypes:
    return AllSimpleTypes(
        i = 100,
        f = 200.0,
        s = "foo",
        b = True,
        d = date(2020, 5, 10),
        dt = datetime(2021, 6, 12, 13, 14, 15, 160),
        t = time(11, 12, 13, 140)
    )

Asserter = Callable[[GraphQLFilter, int, ...], None]
"""
Takes a filter and list of indexes (as varargs).
Performs the query with given filter.
Retrieves entities from the fixture by the indexes.
Compares result of the query and retrieved entities by ID (as sets, unordered).
Asserts that the comparison didn't find differences.
"""

def fixture[E](data_maker: Callable[[], list[E]]):
    def decorate(checker: Callable[[Asserter], None]) -> Callable:
        @wraps(checker)
        def wrapper():
            data = data_maker()
            t: type[E] = type(data[0])
            ctx = ConfigurableContext([
                *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.terminus", "thinking_containers"),
                DockerFromEnvClientFactory
            ])
            with ctx.lifecycle() as idx:
                executor = idx.instance(TaskExecutor)
                repo = idx.instance(TerminusDbStorage).repository(t)
                @executor.stage
                def root():
                    entities = []
                    @executor.step
                    def save_fixture():
                        entities.extend(repo.save(data))
                    @executor.stage
                    def perform_checks():
                        def asserter(q: GraphQLFilter, *idxs: int):
                            found = repo.find().where(q)
                            expected = [data[x] for x in idxs]
                            log.debug(f"Found:    {found}")
                            log.debug(f"Expected: {expected}")
                            # compare by ID, as Terminus cuts down milliseconds and the whole thing goes to... let's say "bed"
                            found_ids = set(x.entity_id() for x in found)
                            expected_ids = set(x.entity_id() for x in expected)
                            assert found_ids == expected_ids, f"Found:\n{'\n'.join(map(str, found))}\nExpected:\n{'\n'.join(map(str, expected))}\nAll data:\n{'\n'.join(map(str, data))}"
                        checker(asserter, entities)
        return wrapper
    return decorate

if "DOCKER_DISABLED" not in current_runtime().facets.by_name:
    def mutate_ints():
        #from 100
        out = [ prototype(), prototype(), prototype() ]
        out[0].i -= 50
        out[2].i += 50
        return out

    @case
    @fixture(mutate_ints)
    def by_int(assert_correct_result_idxs: Asserter, entities: list[AllSimpleTypes]):
        assert_correct_result_idxs({"i": {"eq": "100"}}, 1)
        assert_correct_result_idxs({"i": {"ne": "100"}}, 0, 2)
        assert_correct_result_idxs({"i": {"lt": "100"}}, 0)
        assert_correct_result_idxs({"i": {"le": "100"}}, 0, 1)
        assert_correct_result_idxs({"i": {"gt": "100"}}, 2)
        assert_correct_result_idxs({"i": {"ge": "100"}}, 1, 2)


    def mutate_floats():
        #from 200.0
        out = [prototype(), prototype(), prototype()]
        out[0].f -= 25
        out[2].f += 25
        return out

    @case
    @fixture(mutate_floats)
    def by_float(assert_correct_result_idxs: Asserter, entities: list[AllSimpleTypes]):
        assert_correct_result_idxs({"f": {"eq": "200.0"}}, 1)
        assert_correct_result_idxs({"f": {"ne": "200.0"}}, 0, 2)
        assert_correct_result_idxs({"f": {"lt": "200.0"}}, 0)
        assert_correct_result_idxs({"f": {"le": "200.0"}}, 0, 1)
        assert_correct_result_idxs({"f": {"gt": "200.0"}}, 2)
        assert_correct_result_idxs({"f": {"ge": "200.0"}}, 1, 2)


    def mutate_bools():
        #from True
        out = [prototype(), prototype()]
        out[1].b = False
        return out


    @case
    @fixture(mutate_bools)
    def by_bool(assert_correct_result_idxs: Asserter, entities: list[AllSimpleTypes]):
        assert_correct_result_idxs({"b": {"eq": True}}, 0)
        assert_correct_result_idxs({"b": {"ne": True}}, 1)
        assert_correct_result_idxs({"b": {"eq": False}}, 1)
        assert_correct_result_idxs({"b": {"ne": False}}, 0)


    def mutate_strs():
        #from "foo"
        out = [prototype() for i in range(8)]
        out[1].s = "Foo"
        out[2].s = "fooBar"
        out[3].s = "fo"
        out[4].s = "bar"
        out[5].s = "Bar"
        out[6].s = "gar"
        out[7].s = "Gar"
        return out


    @case
    @fixture(mutate_strs)
    def by_str(assert_correct_result_idxs: Asserter, entities: list[AllSimpleTypes]):
        #todo check sorting of strings representing numbers (e[0].s = "1", e[1].s = "2", ... -1, 100, etc)
        assert_correct_result_idxs({"s": {"eq": "foo"}}, 0)
        assert_correct_result_idxs({"s": {"ne": "foo"}},*range(1, 8))
        # Foo, fo, bar, Bar, Gar
        assert_correct_result_idxs({"s": {"lt": "foo"}}, 1, 3, 4, 5, 7)
        assert_correct_result_idxs({"s": {"le": "foo"}}, 0, 1, 3, 4, 5, 7)
        # fooBar, gar
        assert_correct_result_idxs({"s": {"gt": "foo"}}, 2, 6)
        assert_correct_result_idxs({"s": {"ge": "foo"}}, 0, 2, 6)

        assert_correct_result_idxs({"s": {"startsWith": "fo"}}, 0, 2, 3)

        #clearly, the 'regex' operator means 'search' and not 'match'
        #foo, fooBar, fo
        assert_correct_result_idxs({"s": {"regex": "fo.*"}}, 0, 2, 3)
        assert_correct_result_idxs({"s": {"regex": "fo"}}, 0, 2, 3)
        #foo, Foo, fo
        assert_correct_result_idxs({"s": {"regex": "(f|F)oo?$"}}, 0, 1, 3)
        assert_correct_result_idxs({"s": {"regex": "(f|F)o[o]{0,1}$"}}, 0, 1, 3)
        #foo, Foo, fooBar
        assert_correct_result_idxs({"s": {"regex": "oo"}}, *range(3))
        #nada
        assert_correct_result_idxs({"s": {"regex": "^oo"}})

        #todo what the (pick your own curse) are allOfTerms and anyOfTerms?


    def mutate_datetime():
        #from datetime(2021, 6, 12, 13, 14, 15, 160)
        out = [prototype(), prototype(), prototype()]
        # -1 day
        out[0].dt = datetime(2021, 6, 11, 13, 14, 15, 160)
        # +1 day
        out[2].dt = datetime(2021, 6, 13, 13, 14, 15, 160)
        return out


    #this is the weirdest part of Terminus behaviour I've seen
    # if I run this test locally, it passes - it seems that datetime sorting is reversed
    # if I run this on GH runner (mind you, in both cases I'm using the same docker container), it fails
    # as if it would sort in expected order
    #
    # I think I may need to give up on terminus at all
    #
    # @case
    # @fixture(mutate_datetime)
    # def by_datetime(assert_correct_result_idxs: Asserter, entities: list[AllSimpleTypes]):
    #     pivot = DESER[datetime].serialize(entities[1].dt)
    #     assert_correct_result_idxs({"dt": {"eq": pivot}}, 1)
    #     assert_correct_result_idxs({"dt": {"ne": pivot}}, 0, 2)
    #
    #     #todo this is weird - seems like Terminus compares datetime as "how far int he past"
    #     #you'd expect [1, ]2 for ge/gt and 0[, 1] for lt/le
    #     assert_correct_result_idxs({"dt": {"gt": pivot}}, 0)
    #     assert_correct_result_idxs({"dt": {"ge": pivot}}, 0, 1)
    #
    #     assert_correct_result_idxs({"dt": {"lt": pivot}}, 2)
    #     assert_correct_result_idxs({"dt": {"le": pivot}}, 1, 2)

    def mutate_date():
        #from date(2020, 5, 10)
        out = [prototype(), prototype(), prototype()]
        # -1 day
        out[0].d = date(2020, 5, 9)
        # +1 day
        out[2].d = date(2020, 5, 11)
        return out


    @case
    @fixture(mutate_date)
    def by_date(assert_correct_result_idxs: Asserter, entities: list[AllSimpleTypes]):
        pivot = DESER[date].serialize(entities[1].d)
        # pivot = "2020-05-10"
        assert_correct_result_idxs({"d": {"eq": pivot}}, 1)
        assert_correct_result_idxs({"d": {"ne": pivot}}, 0, 2)

        assert_correct_result_idxs({"d": {"lt": pivot}}, 0)
        assert_correct_result_idxs({"d": {"le": pivot}}, 0, 1)

        assert_correct_result_idxs({"d": {"gt": pivot}}, 2)
        assert_correct_result_idxs({"d": {"ge": pivot}}, 1, 2)
        #GraphQL UI in Terminus dashboard shows that you can apply any string operators to dates, but if you do, you'll get an error


    def mutate_time():
        # from time(11, 12, 13, 140)
        out = [prototype(), prototype(), prototype()]
        # -1 minute
        out[0].t = time(11, 10, 13, 140)
        # +1 minute
        out[2].t = time(11, 13, 13, 140)
        return out


    @case
    @fixture(mutate_time)
    def by_time(assert_correct_result_idxs: Asserter, entities: list[AllSimpleTypes]):
        pivot = DESER[time].serialize(entities[1].t)
        # pivot = "11:12:13.140"
        assert_correct_result_idxs({"t": {"eq": pivot}}, 1)
        assert_correct_result_idxs({"t": {"ne": pivot}}, 0, 2)

        assert_correct_result_idxs({"t": {"lt": pivot}}, 0)
        assert_correct_result_idxs({"t": {"le": pivot}}, 0, 1)

        assert_correct_result_idxs({"t": {"gt": pivot}}, 2)
        assert_correct_result_idxs({"t": {"ge": pivot}}, 1, 2)
        # ditto as date; GraphQL UI hints at str operators, which yield errors
        # todo tests that show that terminus cuts down milliseconds


    class TwoInts(TerminusEntity):
        i: int
        j: int

    def make_grid():
        """
        Makes grid where i is row number and j is column number; indexes or result look like:
        0 | 1 | 2
        3 | 4 | 5
        6 | 7 | 8
        """
        return [
            TwoInts(i=i, j=j)
            for i in range(3)
            for j in range(3)
        ]

    @case
    @fixture(make_grid)
    def and_or(assert_correct_result_idxs: Asserter, entities: list[TwoInts]):
        assert_correct_result_idxs({"_or": [{"i": {"eq": "1"}}, {"j": {"eq": "1"}}]}, 1, 3, 4, 5, 7)
        assert_correct_result_idxs({"_and": [{"i": {"eq": "1"}}, {"j": {"eq": "1"}}]}, 4)
        assert_correct_result_idxs({"_or": [{"i": {"eq": "1"}}, {"i": {"eq": "2"}}]}, 3, 4, 5, 6, 7, 8)
        assert_correct_result_idxs({"_and": [{"i": {"eq": "1"}}, {"i": {"eq": "2"}}]})
        # phrasing the filter like this isn't supported by Terminus
        # assert_correct_result_idxs({"i": {"_or": [{"eq": "1"}, {"eq": "2"}]}}, 3, 4, 5, 6, 7, 8)

        # columns 0 and 2, row 1
        assert_correct_result_idxs({"_or": [{"i": {"eq": "1"}}, {"_not": {"j": {"eq": "1"}}}]}, 0, 2, 3, 4, 5, 6, 8)
        # rows 0 and 2, column 1
        assert_correct_result_idxs({"_or": [{"_not": {"i": {"eq": "1"}}}, {"j": {"eq": "1"}}]}, 0, 1, 2, 4, 6, 7, 8)
        # all but 4
        assert_correct_result_idxs({"_or": [{"_not": {"i": {"eq": "1"}}}, {"_not": {"j": {"eq": "1"}}}]}, 0, 1, 2, 3, 5, 6, 7, 8)


    #todo test negating simple conditions
    @case
    @fixture(make_grid)
    def not_and_or(assert_correct_result_idxs: Asserter, entities: list[TwoInts]):
        assert_correct_result_idxs({"_not": {"_or": [{"i": {"eq": "1"}}, {"j": {"eq": "1"}}]}}, 0, 2, 6, 8)
        assert_correct_result_idxs({"_not": {"_and": [{"i": {"eq": "1"}}, {"j": {"eq": "1"}}]}}, 0, 1, 2, 3, 5, 6, 7, 8)
        assert_correct_result_idxs({"_not": {"_or": [{"i": {"eq": "1"}}, {"i": {"eq": "2"}}]}}, 0, 1, 2)
        assert_correct_result_idxs({"_not": {"_and": [{"i": {"eq": "1"}}, {"i": {"eq": "2"}}]}}, *range(9))

    class PointsToTwoInts(TerminusEntity):
        point: TwoInts

    def indirect_grid():
        """
        The same thing as make_grid(), but packs each TwoInts into PointsToTwoInts
        """
        return [
            PointsToTwoInts(point=x) for x in make_grid()
        ]

    @case
    @fixture(indirect_grid)
    def condition_on_1_1_relation(assert_correct_result_idxs: Asserter, entities: list[PointsToTwoInts]):
        assert_correct_result_idxs({"point": {"i": {"eq": "1"}}}, 3, 4, 5)
        assert_correct_result_idxs({"point": {"i": {"ne": "1"}}}, 0, 1, 2, 6, 7, 8)
        assert_correct_result_idxs({"point": {"i": {"lt": "1"}}}, 0, 1, 2)
        assert_correct_result_idxs({"point": {"i": {"le": "1"}}}, 0, 1, 2, 3, 4, 5)
        assert_correct_result_idxs({"point": {"i": {"gt": "1"}}}, 6, 7, 8)
        assert_correct_result_idxs({"point": {"i": {"ge": "1"}}}, 3, 4, 5, 6, 7, 8)

    class ListOfInts(TerminusEntity):
        ints: list[int]

    def sliding_window():
        return [
            ListOfInts(ints=list(x))
            for x in zip(range(5), range(1, 5))
        ]

    @case
    @fixture(sliding_window)
    def condition_on_value_container(assert_correct_result_idxs: Asserter, entities: list[ListOfInts]):
        assert_correct_result_idxs({"ints": {"someHave": {"gt": "2"}}}, 2, 3)
        assert_correct_result_idxs({"ints": {"allHave": {"gt": "2"}}}, 3)

        assert_correct_result_idxs({"ints": {"someHave": {"eq": "1"}}}, 0, 1)
        assert_correct_result_idxs({"ints": {"allHave": {"eq": "1"}}})

        assert_correct_result_idxs({"ints": {"someHave": {"ne": "1"}}}, 0, 1, 2, 3)
        assert_correct_result_idxs({"ints": {"allHave": {"ne": "1"}}}, 2, 3)

        assert_correct_result_idxs({"_not": {"ints": {"someHave": {"eq": "1"}}}}, 2, 3)
        assert_correct_result_idxs({"_not": {"ints": {"allHave": {"eq": "1"}}}}, 0, 1, 2, 3)

        #todo or, and

        # phrasing the filter like this isn't supported by Terminus
        # assert_correct_result_idxs({"ints": {"someHave": {"_not": {"eq": "1"}}}}, 0, 1, 2, 3)
        # assert_correct_result_idxs({"ints": {"allHave": {"_not": {"eq": "1"}}}}, 2, 3)

        # assert_correct_result_idxs({"ints": {"_not": {"someHave": {"eq": "1"}}}}, 2, 3)
        # assert_correct_result_idxs({"ints": {"_not": {"allHave": {"eq": "1"}}}}, 0, 1, 2, 3)

    class ListOfPairs(TerminusEntity):
        pairs: list[TwoInts]

    def row_column_and_diagonal():
        """
        Same grid as with make_grid(). Result consists of 3 ListOfPairs - first has first row, second has first column and
        third has the diagonal.
        """
        p00 = TwoInts(i=0, j=0)
        p01 = TwoInts(i=0, j=1)
        p02 = TwoInts(i=0, j=2)
        p10 = TwoInts(i=1, j=0)
        p11 = TwoInts(i=1, j=1)
        p20 = TwoInts(i=2, j=0)
        p22 = TwoInts(i=2, j=2)
        return [
            ListOfPairs(pairs=[p00, p01, p02]),
            ListOfPairs(pairs=[p00, p10, p20]),
            ListOfPairs(pairs=[p00, p11, p22])
        ]


    @case
    @fixture(row_column_and_diagonal)
    def condition_on_1_n_relation(assert_correct_result_idxs: Asserter, entities: list[ListOfPairs]):
        #all the commented out variants won't work - they either return incorrect results or response is {"data": null}
        #todo I may wanna try modeling embedded objects as subdocuments instead of relationships
        #anyway, Terminus will work for simple documents, but 1-n relations are screwed - hence another approach to Dolt
        assert_correct_result_idxs({"pairs": {"allHave": {"i": {"eq": "0"}}}}, 0)
        # assert_correct_result_idxs({"pairs": {"allHave": {"j": {"eq": "0"}}}}, 1)
        assert_correct_result_idxs({"pairs": {"allHave": {"_or": [{"i": {"eq": "0"}}]}}}, 0)
        # assert_correct_result_idxs({"pairs": {"allHave": {"_or": [{"i": {"eq": "0"}}, {"j": {"eq": "0"}}]}}}, 0, 1)
        # assert_correct_result_idxs({"_or": [
        #     {"pairs": {"allHave": {"i": {"eq": "0"}}}},
        #     {"pairs": {"allHave": {"j": {"eq": "0"}}}}
        # ]}, 0, 1)
        # assert_correct_result_idxs({"pairs": {"someHave": {"j": {"ge": "1"}}}}, 1, 2)
        # assert_correct_result_idxs({"pairs": {"someHave": {"j": {"eq": "2"}}}}, 1, 2)
        # assert_correct_result_idxs({"_not": {"pairs": {"allHave": {"i": {"eq": "0"}}}}})


if __name__=="__main__":
    run_current_module()
    # by_str()
    # by_datetime()
    # by_date()
    # by_time()
    # and_or()
    # not_and_or()
    # condition_on_1_1_relation()
    # condition_on_value_container()
    # condition_on_1_n_relation()