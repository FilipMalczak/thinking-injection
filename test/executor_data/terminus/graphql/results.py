from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.executor_data.terminus.graphql.model import Holder, Container
from thinking_executor_data.terminus.graphql.results import deserialize_result_data, deserialize_result_response

holder1 = Holder(txt="hello", i=1)
holder1._id = "haJe5iTnc37xVHXy"
holder2 = Holder(txt="world", i=2)
holder2._id = "mVKu2y_fjnFYjWcq"
holder3 = Holder(txt="hello", i=4)
holder3._id = "aeUJZWW4pjvbB_8H"
expected1 = Container(holders=[holder1, holder2])
expected1._id = "0nalZpvmjD4MDbHj"
expected2 = Container(holders=[holder3])
expected2._id = "hbfkMTAXBEXHZYDC"

@case
def test_deserializing_data():

    assert deserialize_result_data(Container, {
        "_id": "terminusdb:///data/Container/0nalZpvmjD4MDbHj",
        "holders": [
            {
                "_id": "terminusdb:///data/Holder/haJe5iTnc37xVHXy",
                "txt": "hello",
                "i": "1"
            },
            {
                "_id": "terminusdb:///data/Holder/mVKu2y_fjnFYjWcq",
                "txt": "world",
                "i": "2"
            }
        ]
    }) == expected1

    assert deserialize_result_data(Container, {
        "_id": "terminusdb:///data/Container/hbfkMTAXBEXHZYDC",
        "holders": [
            {
                "_id": "terminusdb:///data/Holder/aeUJZWW4pjvbB_8H",
                "txt": "hello",
                "i": "4"
            }
        ]
    }) == expected2

    assert deserialize_result_data(list[Container], [
        {
            "_id": "terminusdb:///data/Container/0nalZpvmjD4MDbHj",
            "holders": [
                {
                    "_id": "terminusdb:///data/Holder/haJe5iTnc37xVHXy",
                    "txt": "hello",
                    "i": "1"
                },
                {
                    "_id": "terminusdb:///data/Holder/mVKu2y_fjnFYjWcq",
                    "txt": "world",
                    "i": "2"
                }
            ]
        },
        {
            "_id": "terminusdb:///data/Container/hbfkMTAXBEXHZYDC",
            "holders": [
                {
                    "_id": "terminusdb:///data/Holder/aeUJZWW4pjvbB_8H",
                    "txt": "hello",
                    "i": "4"
                }
            ]
        }
    ]) == [expected1, expected2]

@case
def test_deserializing_response():
    assert deserialize_result_response({
        "data": {
            "Container": [
                {
                    "_id": "terminusdb:///data/Container/0nalZpvmjD4MDbHj",
                    "holders": [
                        {
                            "_id": "terminusdb:///data/Holder/haJe5iTnc37xVHXy",
                            "txt": "hello",
                            "i": "1"
                        },
                        {
                            "_id": "terminusdb:///data/Holder/mVKu2y_fjnFYjWcq",
                            "txt": "world",
                            "i": "2"
                        }
                    ]
                },
                {
                    "_id": "terminusdb:///data/Container/hbfkMTAXBEXHZYDC",
                    "holders": [
                        {
                            "_id": "terminusdb:///data/Holder/aeUJZWW4pjvbB_8H",
                            "txt": "hello",
                            "i": "4"
                        }
                    ]
                }
            ]
        }
    }, Container) == [expected1, expected2]

if __name__=="__main__":
    run_current_module()