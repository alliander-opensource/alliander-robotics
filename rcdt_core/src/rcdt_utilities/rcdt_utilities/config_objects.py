import typing
from dataclasses import dataclass, field

from mashumaro.mixins.json import DataClassJSONMixin


@dataclass
class Config(DataClassJSONMixin):
    def to_str(self) -> str:
        return str(self.to_json())

    @classmethod
    def from_str(cls, data: str) -> typing.Self:
        return cls.from_json(data)


@dataclass
class PlatformConfig(Config):
    namespace: str = ""
    platform_type: str = ""
    position: tuple = (0, 0, 0)
    orientation: tuple = (0, 0, 0)
    parent: str = "none"
    parent_link: str = "none"


@dataclass
class SimulatorConfig(Config):
    load_ui: bool = True
    world: str = "empty.sdf"
    platforms: list[PlatformConfig] = field(default_factory=list)
