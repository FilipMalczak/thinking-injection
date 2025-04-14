from sqlalchemy.orm import DeclarativeBase

#source: https://stackoverflow.com/a/5192374
#todo extract to programming
class classproperty(object):
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)

class SqlAlchemyEntity(DeclarativeBase):
    @classproperty
    def __tablename__(cls):
        return cls.__name__
