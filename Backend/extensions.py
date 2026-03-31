from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, backref, relationship, scoped_session, sessionmaker


class BaseModel(DeclarativeBase):
    query = None


class SQLAlchemy:
    Model = BaseModel
    Column = Column
    Integer = Integer
    String = String
    DateTime = DateTime
    JSON = JSON
    Text = Text
    ForeignKey = ForeignKey
    relationship = staticmethod(relationship)
    backref = staticmethod(backref)

    def __init__(self) -> None:
        self.engine = None
        self.session = scoped_session(sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False))

    def init_app(self, config: object) -> None:
        database_uri = str(getattr(config, "SQLALCHEMY_DATABASE_URI"))
        connect_args = {"check_same_thread": False} if database_uri.startswith("sqlite") else {}
        self.engine = create_engine(database_uri, future=True, connect_args=connect_args)
        self.session.configure(bind=self.engine)
        self.Model.query = self.session.query_property()

    def create_all(self) -> None:
        if self.engine is None:
            raise RuntimeError("Database engine is not initialized.")
        self.Model.metadata.create_all(bind=self.engine)


db = SQLAlchemy()
