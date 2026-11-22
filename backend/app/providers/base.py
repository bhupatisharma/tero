from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProviderResult:
    path: Path
    metadata: dict
