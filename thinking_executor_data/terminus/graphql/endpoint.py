import json

from requests import Session
from requests.auth import HTTPBasicAuth

from thinking_executor_data.terminus.client import TerminusConnectionConfigFactory, TerminusConnectionConfig
from thinking_executor_data.terminus.versioning import TerminusDbVersioning
from thinking_injection.injectable import Injectable


class TerminusDbGraphQLEndpoint(Injectable):
    def __init__(self):
        self.http = Session()
        self.connection_config: TerminusConnectionConfig = None
        self.url_without_branch: str = None
        self.versioning: TerminusDbVersioning = None

    def inject_requirements(self, config_factory: TerminusConnectionConfigFactory, versioning: TerminusDbVersioning) -> None:
        self.connection_config = config_factory.get_terminus_connection_config()
        self.versioning = versioning

    def initialize(self) -> None:
        self.http.auth = HTTPBasicAuth(*self.connection_config.worker)
        self.url_without_branch = f"{self.connection_config.server_url.connection_string}api/graphql/{self.connection_config.team}/{self.connection_config.database}/local/branch/"

    def request(self, gql: str, operation: str | None = None) -> dict:
        url = f"{self.url_without_branch}{self.versioning.current_branch()}"
        payload = {
            "query": gql
        }
        if operation is not None:
            payload["operationName"] = operation
        return self.http.post(url, json=payload).json()
