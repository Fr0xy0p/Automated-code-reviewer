"""
Data structures representing test vectors and inferred parameter types.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, List, Dict, Optional


@dataclass
class TestVector:
    name: str
    category: str
    args: List[Any]
    stdin: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "args": self.args,
            "stdin": self.stdin,
            "description": self.description,
            "tags": self.tags,
        }

