from thinking_runtime.defaults.recognise_runtime import current_runtime
from thinking_tests.current import current_case_name
from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.executor_data.terminus.model import DumbEntity
from test.util import parametrized_case, NamedLambda
from thinking_services.containers.docker_client import DockerFromEnvClientFactory
from thinking_executor.executor import TaskExecutor
from thinking_executor.executor_model import TaskCoordinates, TaskType
from thinking_executor_data.terminus.storage import TerminusDbStorage, TerminusDbRepository, GraphQLFilter
from thinking_executor_data.terminus.versioning import TerminusDbVersioning
from thinking_executor_data.common.writability import WritingDisabledException
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.typeset import from_packages
from thinking_programming.names import make_uuid


def assert_repo_size_is(repo: TerminusDbRepository, size: int):
    assert repo.count().all() == size
    assert repo.count().where({}) == size
    if size == 0:
        assert not repo.exist().where({})
    else:
        assert repo.exist().where({})

def assert_repo_is_empty(repo: TerminusDbRepository):
    assert_repo_size_is(repo, 0)

def assert_cannot_be_found(repo: TerminusDbRepository, q: GraphQLFilter):
    assert repo.count().where(q) == 0
    assert not repo.exist().where(q)
    assert len(list(repo.find().where(q))) == 0

def assert_can_be_found(repo: TerminusDbRepository, q: GraphQLFilter):
    assert repo.count().where(q) > 0
    assert repo.exist().where(q)
    assert len(list(repo.find().where(q))) > 0

def assert_exists(repo: TerminusDbRepository, _id: str):
    assert repo.find().by_id(_id) is not None
    assert len(list(repo.find().by_ids(_id))) == 1
    assert len(list(repo.find().by_ids([_id]))) == 1
    assert repo.count().by_ids(_id) == 1
    assert repo.exist().by_id(_id)
    assert repo.exist().by_ids(_id).all()
    assert repo.exist().by_ids(_id).any()
    assert repo.exist().by_ids([_id]).all()
    assert repo.exist().by_ids([_id]).any()

def assert_doesnt_exists(repo: TerminusDbRepository, _id: str):
    assert repo.find().by_id(_id) is None
    assert len(list(repo.find().by_ids(_id))) == 0
    assert len(list(repo.find().by_ids([_id]))) == 0
    assert repo.count().by_ids(_id) == 0
    assert not repo.exist().by_id(_id)
    assert not repo.exist().by_ids(_id).all()
    assert not repo.exist().by_ids(_id).any()
    assert not repo.exist().by_ids([_id]).all()
    assert not repo.exist().by_ids([_id]).any()

def assert_cannot_be_saved(repo: TerminusDbRepository, e: DumbEntity):
    try:
        repo.save(e)
        assert False
    except WritingDisabledException:
        pass

def expect_coordinates(versioning: TerminusDbVersioning, *coordinates):
    c = TaskCoordinates(*coordinates)
    b = make_uuid(TaskCoordinates.__name__, str(c))
    assert versioning.current_coordinates() == c, f"Expected: {c}, actual: {versioning.current_coordinates()}"
    assert versioning.current_branch() == b, f"Expected: {b}, actual: {versioning.current_branch()}"

if "DOCKER_DISABLED" not in current_runtime().facets.by_name:
    @case
    def no_op_works():
        ctx = ConfigurableContext([
            *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.terminus", "thinking_services.containers"),
            DockerFromEnvClientFactory
        ])
        with ctx.lifecycle() as idx:
            pass

    @case
    def just_create():
        ctx = ConfigurableContext([
            *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.terminus", "thinking_services.containers"),
            DockerFromEnvClientFactory
        ])
        with ctx.lifecycle() as idx:
            executor = idx.instance(TaskExecutor)
            repo = idx.instance(TerminusDbStorage).repository(DumbEntity)
            e = None
            def top_level():
                def a_step():
                    #todo save(one) -> one; save(many) -> many; maybe save_all(many) -> many?
                    nonlocal e
                    assert_repo_is_empty(repo)
                    assert_cannot_be_found(repo, {"txt": {"eq": current_case_name()}})
                    e = list(repo.save(DumbEntity(txt=current_case_name())))[0]
                    assert_repo_size_is(repo, 1)
                    assert_exists(repo, e.entity_id())
                    assert_can_be_found(repo, {"txt": {"eq": current_case_name()}})

                assert_repo_is_empty(repo)
                assert_cannot_be_found(repo, {"txt": {"eq": current_case_name()}})
                assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

                executor.execute_step("step", a_step)

                assert_repo_size_is(repo, 1)
                assert_exists(repo, e.entity_id())
                assert_can_be_found(repo, {"txt": {"eq": current_case_name()}})
                assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

            assert_repo_is_empty(repo)
            assert_cannot_be_found(repo, {"txt": {"eq": current_case_name()}})
            assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

            executor.execute_stage("top", top_level)

            assert_repo_size_is(repo, 1)
            assert_exists(repo, e.entity_id())
            assert_can_be_found(repo, {"txt": {"eq": current_case_name()}})
            assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))



    for deleter in [
        NamedLambda("by id", lambda r, e: r.delete().by_id(e[0].entity_id())),
        NamedLambda("by ids varargs", lambda r, e: r.delete().by_ids(e[0].entity_id())),
        NamedLambda("by ids list", lambda r, e: r.delete().by_ids([e[0].entity_id()])),
        NamedLambda("by where txt=...", lambda r, e: r.delete().where({"txt": {"eq": e[0].txt}}))
    ]:
        @parametrized_case(params=deleter)
        def create_two_then_delete(d):
            ctx = ConfigurableContext([
                *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.terminus", "thinking_services.containers"),
                DockerFromEnvClientFactory
            ])
            with ctx.lifecycle() as idx:
                executor = idx.instance(TaskExecutor)
                repo = idx.instance(TerminusDbStorage).repository(DumbEntity)
                entities = []

                def top_level():
                    def create_step():
                        # todo save(one) -> one; save(many) -> many; maybe save_all(many) -> many?
                        assert_repo_is_empty(repo)
                        assert_cannot_be_found(repo, {"txt": {"eq": current_case_name()}})
                        entities.extend(repo.save(DumbEntity(txt=current_case_name()+"1")))
                        entities.extend(repo.save(DumbEntity(txt=current_case_name()+"2")))
                        assert_repo_size_is(repo, 2)
                        assert_exists(repo, entities[0].entity_id())
                        assert_exists(repo, entities[1].entity_id())
                        assert_can_be_found(repo, {"txt": {"eq": entities[0].txt}})
                        assert_can_be_found(repo, {"txt": {"eq": entities[1].txt}})

                    def delete_step():
                        assert_repo_size_is(repo, 2)
                        assert_exists(repo, entities[0].entity_id())
                        assert_exists(repo, entities[1].entity_id())
                        assert_can_be_found(repo, {"txt": {"eq": entities[0].txt}})
                        assert_can_be_found(repo, {"txt": {"eq": entities[1].txt}})

                        d(repo, entities)

                        assert_repo_size_is(repo, 1)
                        assert_doesnt_exists(repo, entities[0].entity_id())
                        assert_exists(repo, entities[1].entity_id())
                        assert_cannot_be_found(repo, {"txt": {"eq": entities[0].txt}})
                        assert_can_be_found(repo, {"txt": {"eq": entities[1].txt}})

                    assert_repo_is_empty(repo)
                    assert_cannot_be_found(repo, {"txt": {"eq": current_case_name()}})
                    assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

                    executor.execute_step("create", create_step)

                    assert_repo_size_is(repo, 2)
                    assert_exists(repo, entities[0].entity_id())
                    assert_exists(repo, entities[1].entity_id())
                    assert_can_be_found(repo, {"txt": {"eq": current_case_name() + "1"}})
                    assert_can_be_found(repo, {"txt": {"eq": current_case_name() + "2"}})
                    #todo assert cannot be deleted

                    executor.execute_step("delete", delete_step)

                    assert_repo_size_is(repo, 1)
                    assert_doesnt_exists(repo, entities[0].entity_id())
                    assert_exists(repo, entities[1].entity_id())
                    assert_cannot_be_found(repo, {"txt": {"eq": entities[0].txt}})
                    assert_can_be_found(repo, {"txt": {"eq": entities[1].txt}})


                assert_repo_is_empty(repo)
                assert_cannot_be_found(repo, {"txt": {"eq": current_case_name()}})
                assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

                executor.execute_stage("top", top_level)

                assert_repo_size_is(repo, 1)
                assert_doesnt_exists(repo, entities[0].entity_id())
                assert_exists(repo, entities[1].entity_id())
                assert_cannot_be_found(repo, {"txt": {"eq": entities[0].txt}})
                assert_can_be_found(repo, {"txt": {"eq": entities[1].txt}})

    @case
    def branches_are_correct():
        ctx = ConfigurableContext([
            *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.terminus", "thinking_services.containers"),
            DockerFromEnvClientFactory
        ])
        with ctx.lifecycle() as idx:
            executor = idx.instance(TaskExecutor)
            versioning = idx.instance(TerminusDbVersioning)

            def top():
                def first():
                    expect_coordinates(versioning, ["top", "first"], [0, 0], TaskType.STEP)
                def second():
                    def sub1():
                        expect_coordinates(versioning, ["top", "second", "sub1"], [0, 1, 0], TaskType.STEP)
                    def sub2():
                        expect_coordinates(versioning, ["top", "second", "sub2"], [0, 1, 1], TaskType.STEP)
                    expect_coordinates(versioning, ["top", "first"], [0, 0], TaskType.STEP)
                    executor.execute_step("sub1", sub1)
                    expect_coordinates(versioning, ["top", "second", "sub1"], [0, 1, 0], TaskType.STEP)
                    executor.execute_step("sub2", sub2)
                    expect_coordinates(versioning, ["top", "second", "sub2"], [0, 1, 1], TaskType.STEP)
                def third():
                    expect_coordinates(versioning, ["top", "third"], [0, 2], TaskType.STEP)
                assert versioning.current_branch() == "main"
                assert versioning.current_coordinates() == None
                executor.execute_step("first", first)
                expect_coordinates(versioning, ["top", "first"], [0, 0], TaskType.STEP)
                executor.execute_stage("second", second)
                expect_coordinates(versioning, ["top", "second", "sub2"], [0, 1, 1], TaskType.STEP)
                executor.execute_step("third", third)
                expect_coordinates(versioning, ["top", "third"], [0, 2], TaskType.STEP)

            assert versioning.current_branch() == "main"
            executor.execute_stage("top", top)
            expect_coordinates(versioning, ["top", "third"], [0, 2], TaskType.STEP)

if __name__=="__main__":
    run_current_module()
    # no_op_works()