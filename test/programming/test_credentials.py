from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_programming.credentials import Credentials


@case
def test_nones():
    assert str(Credentials(None, None)) == "Credentials(username=None, password=None)"
    assert str(Credentials("x", None)) == "Credentials(username='x', password=None)"

@case
def test_password_masking():
    assert str(Credentials("x", "y")) == "Credentials(username='x', password='*')"
    assert str(Credentials("x", "yy")) == "Credentials(username='x', password='**')"
    assert str(Credentials("x", "abc")) == "Credentials(username='x', password='a*c')"

if __name__=="__main__":
    run_current_module()