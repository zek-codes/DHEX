"""Recipe and user management for the DHEX cooking and baking system."""

import json
import os
from typing import List, Optional

from src.models import Recipe, RecipeCategory, User


class RecipeManager:
    """Manages recipes and users, with optional JSON file persistence."""

    def __init__(self, storage_path: Optional[str] = None):
        self._recipes: dict[str, Recipe] = {}
        self._users: dict[str, User] = {}
        self._storage_path = storage_path
        if storage_path and os.path.exists(storage_path):
            self._load(storage_path)

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------

    def add_user(self, user: User) -> User:
        """Register a new user (baker/cook)."""
        if user.email in {u.email for u in self._users.values()}:
            raise ValueError(f"A user with email '{user.email}' already exists.")
        self._users[user.id] = user
        self._save()
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email address."""
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def list_users(self) -> List[User]:
        """Return all registered users."""
        return list(self._users.values())

    def update_user(self, user: User) -> User:
        """Update an existing user's information."""
        if user.id not in self._users:
            raise ValueError(f"User with ID '{user.id}' not found.")
        self._users[user.id] = user
        self._save()
        return user

    def delete_user(self, user_id: str) -> None:
        """Remove a user (and all their recipes) from the system."""
        if user_id not in self._users:
            raise ValueError(f"User with ID '{user_id}' not found.")
        del self._users[user_id]
        # Remove the user's recipes
        to_delete = [r.id for r in self._recipes.values() if r.author_id == user_id]
        for recipe_id in to_delete:
            del self._recipes[recipe_id]
        self._save()

    # ------------------------------------------------------------------
    # Recipe management
    # ------------------------------------------------------------------

    def add_recipe(self, recipe: Recipe) -> Recipe:
        """Add a new recipe to the system."""
        if recipe.author_id not in self._users:
            raise ValueError(
                f"Author with ID '{recipe.author_id}' not found. "
                "Register the user before adding recipes."
            )
        self._recipes[recipe.id] = recipe
        self._save()
        return recipe

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """Retrieve a recipe by ID."""
        return self._recipes.get(recipe_id)

    def list_recipes(
        self,
        author_id: Optional[str] = None,
        category: Optional[RecipeCategory] = None,
    ) -> List[Recipe]:
        """Return recipes, optionally filtered by author and/or category."""
        results = list(self._recipes.values())
        if author_id is not None:
            results = [r for r in results if r.author_id == author_id]
        if category is not None:
            results = [r for r in results if r.category == category]
        return results

    def search_recipes(self, keyword: str) -> List[Recipe]:
        """Search recipes by keyword in title or ingredients."""
        keyword_lower = keyword.lower()
        return [
            r
            for r in self._recipes.values()
            if keyword_lower in r.title.lower()
            or any(keyword_lower in i.name.lower() for i in r.ingredients)
        ]

    def update_recipe(self, recipe: Recipe) -> Recipe:
        """Update an existing recipe."""
        if recipe.id not in self._recipes:
            raise ValueError(f"Recipe with ID '{recipe.id}' not found.")
        self._recipes[recipe.id] = recipe
        self._save()
        return recipe

    def delete_recipe(self, recipe_id: str) -> None:
        """Remove a recipe from the system."""
        if recipe_id not in self._recipes:
            raise ValueError(f"Recipe with ID '{recipe_id}' not found.")
        del self._recipes[recipe_id]
        self._save()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _save(self) -> None:
        if not self._storage_path:
            return
        data = {
            "users": {uid: u.to_dict() for uid, u in self._users.items()},
            "recipes": {rid: r.to_dict() for rid, r in self._recipes.items()},
        }
        with open(self._storage_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def _load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
        if not content:
            return
        data = json.loads(content)
        self._users = {uid: User.from_dict(u) for uid, u in data.get("users", {}).items()}
        self._recipes = {
            rid: Recipe.from_dict(r) for rid, r in data.get("recipes", {}).items()
        }
