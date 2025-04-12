from thinking_tests.current import current_case_name
from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.executor_data.dolt.model import DumbEntity
from test.util import parametrized_case, NamedLambda
from thinking_executor.executor import TaskExecutor
from thinking_executor.executor_model import TaskCoordinates, TaskType
from thinking_executor_data.common.writability import WritingDisabledException
from thinking_executor_data.dolt.sqlalchemy.storage import DoltRepository, SQLFilter, DoltStorage
from thinking_executor_data.dolt.sqlalchemy.versioning import SqlAlchemyDoltVersioning
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.typeset import from_packages
from thinking_programming.names import make_uuid
from thinking_programming.tracing import traced


@traced
def assert_repo_size_is(repo: DoltRepository, size: int):
    assert repo.count().all() == size
    assert repo.count().where(None) == size
    if size == 0:
        assert not repo.exist().where(None)
    else:
        assert repo.exist().where(None)

@traced
def assert_repo_is_empty(repo: DoltRepository):
    assert_repo_size_is(repo, 0)

@traced
def assert_cannot_be_found(repo: DoltRepository, q: SQLFilter):
    assert repo.count().where(q) == 0
    assert not repo.exist().where(q)
    assert len(list(repo.find().where(q))) == 0

@traced
def assert_can_be_found(repo: DoltRepository, q: SQLFilter):
    assert repo.count().where(q) > 0
    assert repo.exist().where(q)
    assert len(list(repo.find().where(q))) > 0

@traced
def assert_exists(repo: DoltRepository, _id: int):
    assert repo.find().by_id(_id) is not None
    assert len(list(repo.find().by_ids(_id))) == 1
    assert len(list(repo.find().by_ids([_id]))) == 1
    assert repo.count().by_ids(_id) == 1
    assert repo.exist().by_id(_id)
    assert repo.exist().by_ids(_id).all()
    assert repo.exist().by_ids(_id).any()
    assert repo.exist().by_ids([_id]).all()
    assert repo.exist().by_ids([_id]).any()
    #todo where(type.id == _id); ditto in reruns and terminus tests


@traced
def assert_doesnt_exists(repo: DoltRepository, _id: int):
    assert repo.find().by_id(_id) is None
    assert len(list(repo.find().by_ids(_id))) == 0
    assert len(list(repo.find().by_ids([_id]))) == 0
    assert repo.count().by_ids(_id) == 0
    assert not repo.exist().by_id(_id)
    assert not repo.exist().by_ids(_id).all()
    assert not repo.exist().by_ids(_id).any()
    assert not repo.exist().by_ids([_id]).all()
    assert not repo.exist().by_ids([_id]).any()

@traced
def assert_cannot_be_saved(repo: DoltRepository, e: DumbEntity):
    try:
        repo.save(e)
        assert False
    except WritingDisabledException:
        pass
    try:
        repo.save([e])
        assert False
    except WritingDisabledException:
        pass
    try:
        repo.save_one(e)
        assert False
    except WritingDisabledException:
        pass

@traced
def expect_coordinates(versioning: SqlAlchemyDoltVersioning, *coordinates):
    c = TaskCoordinates(*coordinates)
    b = make_uuid(TaskCoordinates.__name__, str(c))
    assert versioning.current_coordinates() == c, f"Expected: {c}, actual: {versioning.current_coordinates()}"
    assert versioning.current_branch() == b, f"Expected: {b}, actual: {versioning.current_branch()}"

@case
def no_op_works():
    ctx = ConfigurableContext([
        *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.dolt", "thinking_containers")
    ])
    with ctx.lifecycle() as idx:
        pass

@case
def just_create():
    ctx = ConfigurableContext([
        *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.dolt", "thinking_containers")
    ])
    with ctx.lifecycle() as idx:
        executor = idx.instance(TaskExecutor)
        repo = idx.instance(DoltStorage).repository(DumbEntity)
        v = idx.instance(SqlAlchemyDoltVersioning)
        e = None
        q = DumbEntity.txt == current_case_name()
        @traced
        def top_level():
            @traced
            def a_step():
                #todo save(one) -> one; save(many) -> many; maybe save_all(many) -> many?
                nonlocal e
                assert_repo_is_empty(repo)
                assert_cannot_be_found(repo, q)
                e = repo.save_one(DumbEntity(txt=current_case_name()))
                assert_repo_size_is(repo, 1)
                assert_exists(repo, e.id_)
                assert_can_be_found(repo, q)

            assert_repo_is_empty(repo)
            assert_cannot_be_found(repo, q)
            assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

            executor.execute_step("step", a_step)

            assert_repo_size_is(repo, 1)
            assert_exists(repo, e.id_)
            assert_can_be_found(repo, q)
            assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

        assert_repo_is_empty(repo)
        assert_cannot_be_found(repo, q)
        assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

        executor.execute_stage("top", top_level)

        assert_repo_size_is(repo, 1)
        assert_exists(repo, e.id_)
        assert_can_be_found(repo, q)
        assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))



for deleter in [
    NamedLambda("by id", lambda r, e: r.delete().by_id(e[0].id_)),
    NamedLambda("by ids varargs", lambda r, e: r.delete().by_ids(e[0].id_)),
    NamedLambda("by ids list", lambda r, e: r.delete().by_ids([e[0].id_])),
    NamedLambda("by where txt=...", lambda r, e: r.delete().where(DumbEntity.txt == e[0].txt))
]:
    @parametrized_case(params=deleter)
    def create_two_then_delete(d):
        ctx = ConfigurableContext([
            *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.dolt", "thinking_containers")
        ])
        with ctx.lifecycle() as idx:
            executor = idx.instance(TaskExecutor)
            repo = idx.instance(DoltStorage).repository(DumbEntity)
            e1 = DumbEntity(txt=current_case_name()+"1")
            e2 = DumbEntity(txt=current_case_name()+"2")
            entities = []

            def top_level():
                def create_step():
                    # todo save(one) -> one; save(many) -> many; maybe save_all(many) -> many?
                    assert_repo_is_empty(repo)
                    assert_cannot_be_found(repo, DumbEntity.txt == e1.txt)
                    assert_cannot_be_found(repo, DumbEntity.txt == e2.txt)
                    saved = repo.save(e1, e2)
                    entities.extend(saved)
                    assert_repo_size_is(repo, 2)
                    assert_exists(repo, entities[0].id_)
                    assert_exists(repo, entities[1].id_)
                    assert_can_be_found(repo, DumbEntity.txt == entities[0].txt)
                    assert_can_be_found(repo, DumbEntity.txt == entities[1].txt)

                def delete_step():
                    assert_repo_size_is(repo, 2)
                    assert_exists(repo, entities[0].id_)
                    assert_exists(repo, entities[1].id_)
                    assert_can_be_found(repo, DumbEntity.txt == entities[0].txt)
                    assert_can_be_found(repo, DumbEntity.txt == entities[1].txt)

                    d(repo, entities)

                    assert_repo_size_is(repo, 1)
                    assert_doesnt_exists(repo, entities[0].id_)
                    assert_exists(repo, entities[1].id_)
                    assert_cannot_be_found(repo, DumbEntity.txt == entities[0].txt)
                    assert_can_be_found(repo, DumbEntity.txt == entities[1].txt)

                assert_repo_is_empty(repo)

                assert_cannot_be_found(repo, DumbEntity.txt == e1.txt)
                assert_cannot_be_found(repo, DumbEntity.txt == e2.txt)
                assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

                executor.execute_step("create", create_step)

                assert_repo_size_is(repo, 2)
                assert_exists(repo, entities[0].id_)
                assert_exists(repo, entities[1].id_)
                assert_can_be_found(repo, DumbEntity.txt == entities[0].txt)
                assert_can_be_found(repo, DumbEntity.txt == entities[1].txt)
                #todo assert cannot be deleted

                executor.execute_step("delete", delete_step)

                assert_repo_size_is(repo, 1)
                assert_doesnt_exists(repo, entities[0].id_)
                assert_exists(repo, entities[1].id_)
                assert_cannot_be_found(repo, DumbEntity.txt == entities[0].txt)
                assert_can_be_found(repo, DumbEntity.txt == entities[1].txt)


            assert_repo_is_empty(repo)

            assert_cannot_be_found(repo, DumbEntity.txt == e1.txt)
            assert_cannot_be_found(repo, DumbEntity.txt == e2.txt)
            assert_cannot_be_saved(repo, DumbEntity(txt="should fail"))

            executor.execute_stage("top", top_level)

            assert_repo_size_is(repo, 1)
            assert_doesnt_exists(repo, entities[0].id_)
            assert_exists(repo, entities[1].id_)
            assert_cannot_be_found(repo, DumbEntity.txt == entities[0].txt)
            assert_can_be_found(repo, DumbEntity.txt == entities[1].txt)

@case
def branches_are_correct():
    ctx = ConfigurableContext([
        *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.dolt", "thinking_containers")
    ])
    with ctx.lifecycle() as idx:
        executor = idx.instance(TaskExecutor)
        versioning = idx.instance(SqlAlchemyDoltVersioning)

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
    # just_create()
    # create_two_then_delete()