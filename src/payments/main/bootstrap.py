"""Application bootstrap utilities."""

import orjson
from psycopg.types.json import set_json_dumps, set_json_loads


def setup_json() -> None:
    """Set orjson as the global JSONB serializer and deserializer for psycopg."""
    set_json_dumps(orjson.dumps)
    set_json_loads(orjson.loads)
