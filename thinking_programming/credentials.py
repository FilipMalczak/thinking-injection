from typing import NamedTuple


class Credentials(NamedTuple):
    username: str
    password: str

    def __str__(self):
        return f"Credentials(username={self.username}, password={self.masked_password})"

    @property
    def masked_password(self):
        if self.password is None:
            return self.password
        if len(self.password) < 3:
            return "*"*len(self.password)
        out = self.password[0]
        out += "*"*(len(self.password)-2)
        out += self.password[-1]
        return out