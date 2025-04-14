from typing import NamedTuple


class Credentials(NamedTuple):
    username: str
    password: str

    def __str__(self):
        u = "'"+self.username+"'" if self.username is not None else None
        p = "'"+self.masked_password+"'" if self.masked_password is not None else None
        return f"Credentials(username={u}, password={p})"

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

