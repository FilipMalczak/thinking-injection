from thinking_executor_data.terminus.base import TerminusEntity


class Holder(TerminusEntity):
    i: int
    txt: str

class Container(TerminusEntity):
    holders: list[Holder]


