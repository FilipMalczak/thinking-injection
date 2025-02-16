from thinking_executor.data.tiny_model import TinyConfiguration, TinyDBParameters
from thinking_reflection.discovery import discover


@discover
class TinyDbConfig(TinyConfiguration):
    def get_tinydb_parameters(self) -> TinyDBParameters:
        return TinyDBParameters("./kmeans.json")