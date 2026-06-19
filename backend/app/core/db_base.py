from datetime import datetime
from typing import Annotated
from uuid import UUID

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, mapped_column

from app.core.ids import new_uuid7


class Base(DeclarativeBase):
    pass


UUIDPk = Annotated[
    UUID,
    mapped_column(primary_key=True, default=new_uuid7),
]

TimestampTZ = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now()),
]
