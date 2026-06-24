"""Base entity module."""

from dataclasses import dataclass


@dataclass(kw_only=True)
class Entity[OIDType]:
    """Base class for all domain entities."""

    oid: OIDType
