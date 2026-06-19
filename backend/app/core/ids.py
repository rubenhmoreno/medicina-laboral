import uuid

from uuid_extensions import uuid7  # type: ignore[import-untyped]  # uuid7 package


def new_uuid7() -> uuid.UUID:
    return uuid7()  # type: ignore[no-any-return]
