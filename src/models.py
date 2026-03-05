"""Data models for the DHEX cooking and baking system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid
import datetime


class RecipeCategory(str, Enum):
    BAKING = "baking"
    COOKING = "cooking"


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class User:
    """Represents an individual baker or cook."""

    name: str
    email: str
    skill_level: SkillLevel = SkillLevel.BEGINNER
    dietary_preferences: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "skill_level": self.skill_level.value,
            "dietary_preferences": self.dietary_preferences,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            skill_level=SkillLevel(data["skill_level"]),
            dietary_preferences=data.get("dietary_preferences", []),
            created_at=data.get("created_at", ""),
        )


@dataclass
class Ingredient:
    """Represents a single ingredient in a recipe."""

    name: str
    quantity: str
    unit: Optional[str] = None

    def to_dict(self) -> dict:
        return {"name": self.name, "quantity": self.quantity, "unit": self.unit}

    @classmethod
    def from_dict(cls, data: dict) -> "Ingredient":
        return cls(name=data["name"], quantity=data["quantity"], unit=data.get("unit"))

    def __str__(self) -> str:
        if self.unit:
            return f"{self.quantity} {self.unit} {self.name}"
        return f"{self.quantity} {self.name}"


@dataclass
class Recipe:
    """Represents a cooking or baking recipe."""

    title: str
    category: RecipeCategory
    ingredients: List[Ingredient]
    instructions: List[str]
    author_id: str
    prep_time_minutes: int = 0
    cook_time_minutes: int = 0
    servings: int = 1
    notes: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    @property
    def total_time_minutes(self) -> int:
        return self.prep_time_minutes + self.cook_time_minutes

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "instructions": self.instructions,
            "author_id": self.author_id,
            "prep_time_minutes": self.prep_time_minutes,
            "cook_time_minutes": self.cook_time_minutes,
            "servings": self.servings,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Recipe":
        return cls(
            id=data["id"],
            title=data["title"],
            category=RecipeCategory(data["category"]),
            ingredients=[Ingredient.from_dict(i) for i in data["ingredients"]],
            instructions=data["instructions"],
            author_id=data["author_id"],
            prep_time_minutes=data.get("prep_time_minutes", 0),
            cook_time_minutes=data.get("cook_time_minutes", 0),
            servings=data.get("servings", 1),
            notes=data.get("notes"),
            created_at=data.get("created_at", ""),
        )
