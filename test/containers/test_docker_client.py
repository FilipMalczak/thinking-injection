import urllib
from http.client import HTTPException
from logging import getLogger
from urllib.error import URLError

from thinking_runtime.defaults.recognise_runtime import current_runtime
from thinking_tests.current import current_case_name
from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_containers.docker_client import DockerFromEnvClientFactory, UnixSocketDockerClientFactory
from thinking_containers.protocol import ContainerClient
from thinking_injection.context.simple import SimpleContext
from thinking_injection.typeset import from_package

log = getLogger(__name__)

if "DOCKER_DISABLED" not in current_runtime().facets.by_name:
    #fixme this is a good candidate for parametrized case

    @case
    def test_running_echo_server_with_from_env():
        with SimpleContext([*from_package("thinking_containers"), DockerFromEnvClientFactory]).lifecycle() as idx:
            client = idx.instance(ContainerClient)
            container = client.run("hashicorp/http-echo", cmd=f"-text {current_case_name()}", ports={5678: 5678})
            try:
                TRIES = 3
                ok = False
                txt = None
                for i in range(TRIES):
                    try:
                        resp = urllib.request.urlopen("http://localhost:5678")
                        if resp.status == 200:
                            ok = True
                            txt = resp.read().decode("utf-8").strip()
                            break
                    except HTTPException | URLError:
                        pass
                assert ok
                assert txt == current_case_name(), f"Actual response: '{txt}'"
            finally:
                container.stop()
        try:
            resp = urllib.request.urlopen("http://localhost:5678")
            assert False
        except URLError:
            assert True

    @case
    def test_running_echo_server_with_unix_socker():
        with SimpleContext([*from_package("thinking_containers"), UnixSocketDockerClientFactory]).lifecycle() as idx:
            client = idx.instance(ContainerClient)
            container = client.run("hashicorp/http-echo", cmd=f"-text {current_case_name()}", ports={5678: 5678})
            try:
                TRIES = 3
                ok = False
                txt = None
                for i in range(TRIES):
                    try:
                        resp = urllib.request.urlopen("http://localhost:5678")
                        if resp.status == 200:
                            ok = True
                            txt = resp.read().decode("utf-8").strip()
                            break
                    except HTTPException | URLError:
                        pass
                assert ok
                assert txt == current_case_name(), f"Actual response: '{txt}'"
            finally:
                container.stop()
        try:
            resp = urllib.request.urlopen("http://localhost:5678")
            assert False
        except URLError:
            assert True


    if __name__ == "__main__":
        run_current_module()