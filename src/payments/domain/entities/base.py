from dataclasses import dataclass


@dataclass(kw_only=True)
class Entity[OIDType]:
    oid: OIDType
