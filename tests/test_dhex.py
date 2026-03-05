"""Unit tests for the DHEX cooking and baking system."""

import os
import tempfile
import unittest

from src.models import Ingredient, Recipe, RecipeCategory, SkillLevel, User
from src.recipe_manager import RecipeManager


def _make_user(**kwargs) -> User:
    defaults = dict(
        name="Alice Baker",
        email="alice@example.com",
        skill_level=SkillLevel.INTERMEDIATE,
    )
    defaults.update(kwargs)
    return User(**defaults)


def _make_recipe(author_id: str, **kwargs) -> Recipe:
    defaults = dict(
        title="Classic Sourdough",
        category=RecipeCategory.BAKING,
        ingredients=[Ingredient(name="flour", quantity="500", unit="grams")],
        instructions=["Mix flour with water.", "Knead for 10 minutes.", "Bake at 230°C."],
        author_id=author_id,
        prep_time_minutes=20,
        cook_time_minutes=40,
        servings=8,
    )
    defaults.update(kwargs)
    return Recipe(**defaults)


class TestUserModel(unittest.TestCase):
    def test_user_creation_defaults(self):
        user = User(name="Bob", email="bob@example.com")
        self.assertEqual(user.name, "Bob")
        self.assertEqual(user.email, "bob@example.com")
        self.assertEqual(user.skill_level, SkillLevel.BEGINNER)
        self.assertEqual(user.dietary_preferences, [])
        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user.created_at)

    def test_user_serialisation_round_trip(self):
        user = _make_user(dietary_preferences=["gluten-free"])
        restored = User.from_dict(user.to_dict())
        self.assertEqual(user.id, restored.id)
        self.assertEqual(user.name, restored.name)
        self.assertEqual(user.email, restored.email)
        self.assertEqual(user.skill_level, restored.skill_level)
        self.assertEqual(user.dietary_preferences, restored.dietary_preferences)


class TestIngredientModel(unittest.TestCase):
    def test_ingredient_str_with_unit(self):
        ing = Ingredient(name="flour", quantity="2", unit="cups")
        self.assertEqual(str(ing), "2 cups flour")

    def test_ingredient_str_without_unit(self):
        ing = Ingredient(name="eggs", quantity="3")
        self.assertEqual(str(ing), "3 eggs")

    def test_ingredient_serialisation_round_trip(self):
        ing = Ingredient(name="butter", quantity="100", unit="grams")
        restored = Ingredient.from_dict(ing.to_dict())
        self.assertEqual(ing.name, restored.name)
        self.assertEqual(ing.quantity, restored.quantity)
        self.assertEqual(ing.unit, restored.unit)


class TestRecipeModel(unittest.TestCase):
    def test_total_time(self):
        recipe = _make_recipe(author_id="x", prep_time_minutes=15, cook_time_minutes=45)
        self.assertEqual(recipe.total_time_minutes, 60)

    def test_recipe_serialisation_round_trip(self):
        user = _make_user()
        recipe = _make_recipe(author_id=user.id)
        restored = Recipe.from_dict(recipe.to_dict())
        self.assertEqual(recipe.id, restored.id)
        self.assertEqual(recipe.title, restored.title)
        self.assertEqual(recipe.category, restored.category)
        self.assertEqual(len(recipe.ingredients), len(restored.ingredients))
        self.assertEqual(recipe.instructions, restored.instructions)
        self.assertEqual(recipe.servings, restored.servings)


class TestRecipeManager(unittest.TestCase):
    def setUp(self):
        self.manager = RecipeManager()

    # --- user operations ---

    def test_add_and_get_user(self):
        user = _make_user()
        self.manager.add_user(user)
        retrieved = self.manager.get_user(user.id)
        self.assertEqual(retrieved.name, user.name)

    def test_duplicate_email_raises(self):
        self.manager.add_user(_make_user())
        with self.assertRaises(ValueError):
            self.manager.add_user(_make_user())  # same email

    def test_get_user_by_email(self):
        user = _make_user()
        self.manager.add_user(user)
        found = self.manager.get_user_by_email(user.email)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, user.id)

    def test_list_users(self):
        self.manager.add_user(_make_user(email="a@example.com"))
        self.manager.add_user(_make_user(email="b@example.com", name="Bob"))
        self.assertEqual(len(self.manager.list_users()), 2)

    def test_update_user(self):
        user = _make_user()
        self.manager.add_user(user)
        user.name = "Alice Updated"
        self.manager.update_user(user)
        self.assertEqual(self.manager.get_user(user.id).name, "Alice Updated")

    def test_update_nonexistent_user_raises(self):
        user = _make_user()  # not added
        with self.assertRaises(ValueError):
            self.manager.update_user(user)

    def test_delete_user_removes_their_recipes(self):
        user = _make_user()
        self.manager.add_user(user)
        recipe = _make_recipe(author_id=user.id)
        self.manager.add_recipe(recipe)
        self.manager.delete_user(user.id)
        self.assertIsNone(self.manager.get_user(user.id))
        self.assertIsNone(self.manager.get_recipe(recipe.id))

    def test_delete_nonexistent_user_raises(self):
        with self.assertRaises(ValueError):
            self.manager.delete_user("no-such-id")

    # --- recipe operations ---

    def test_add_recipe_without_user_raises(self):
        recipe = _make_recipe(author_id="ghost")
        with self.assertRaises(ValueError):
            self.manager.add_recipe(recipe)

    def test_add_and_get_recipe(self):
        user = _make_user()
        self.manager.add_user(user)
        recipe = _make_recipe(author_id=user.id)
        self.manager.add_recipe(recipe)
        retrieved = self.manager.get_recipe(recipe.id)
        self.assertEqual(retrieved.title, recipe.title)

    def test_list_recipes_filter_by_category(self):
        user = _make_user()
        self.manager.add_user(user)
        self.manager.add_recipe(_make_recipe(author_id=user.id, title="Bread", category=RecipeCategory.BAKING))
        self.manager.add_recipe(_make_recipe(author_id=user.id, title="Pasta", category=RecipeCategory.COOKING))
        baking = self.manager.list_recipes(category=RecipeCategory.BAKING)
        cooking = self.manager.list_recipes(category=RecipeCategory.COOKING)
        self.assertEqual(len(baking), 1)
        self.assertEqual(len(cooking), 1)
        self.assertEqual(baking[0].title, "Bread")
        self.assertEqual(cooking[0].title, "Pasta")

    def test_list_recipes_filter_by_author(self):
        user1 = _make_user(email="u1@example.com")
        user2 = _make_user(email="u2@example.com", name="Bob")
        self.manager.add_user(user1)
        self.manager.add_user(user2)
        self.manager.add_recipe(_make_recipe(author_id=user1.id, title="Cake"))
        self.manager.add_recipe(_make_recipe(author_id=user2.id, title="Pie"))
        self.assertEqual(len(self.manager.list_recipes(author_id=user1.id)), 1)
        self.assertEqual(len(self.manager.list_recipes(author_id=user2.id)), 1)

    def test_search_recipes_by_title(self):
        user = _make_user()
        self.manager.add_user(user)
        self.manager.add_recipe(_make_recipe(author_id=user.id, title="Chocolate Cake"))
        self.manager.add_recipe(_make_recipe(author_id=user.id, title="Vanilla Muffins"))
        results = self.manager.search_recipes("chocolate")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Chocolate Cake")

    def test_search_recipes_by_ingredient(self):
        user = _make_user()
        self.manager.add_user(user)
        recipe = _make_recipe(
            author_id=user.id,
            title="Cheesy Bread",
            ingredients=[Ingredient(name="cheddar cheese", quantity="100", unit="grams")],
        )
        self.manager.add_recipe(recipe)
        results = self.manager.search_recipes("cheddar")
        self.assertEqual(len(results), 1)

    def test_update_recipe(self):
        user = _make_user()
        self.manager.add_user(user)
        recipe = _make_recipe(author_id=user.id)
        self.manager.add_recipe(recipe)
        recipe.title = "Updated Title"
        self.manager.update_recipe(recipe)
        self.assertEqual(self.manager.get_recipe(recipe.id).title, "Updated Title")

    def test_update_nonexistent_recipe_raises(self):
        user = _make_user()
        self.manager.add_user(user)
        recipe = _make_recipe(author_id=user.id)  # not added
        with self.assertRaises(ValueError):
            self.manager.update_recipe(recipe)

    def test_delete_recipe(self):
        user = _make_user()
        self.manager.add_user(user)
        recipe = _make_recipe(author_id=user.id)
        self.manager.add_recipe(recipe)
        self.manager.delete_recipe(recipe.id)
        self.assertIsNone(self.manager.get_recipe(recipe.id))

    def test_delete_nonexistent_recipe_raises(self):
        with self.assertRaises(ValueError):
            self.manager.delete_recipe("no-such-id")

    # --- persistence ---

    def test_persistence_round_trip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            path = tmp.name
        try:
            mgr1 = RecipeManager(storage_path=path)
            user = _make_user()
            mgr1.add_user(user)
            recipe = _make_recipe(author_id=user.id)
            mgr1.add_recipe(recipe)

            mgr2 = RecipeManager(storage_path=path)
            self.assertEqual(len(mgr2.list_users()), 1)
            self.assertEqual(len(mgr2.list_recipes()), 1)
            self.assertEqual(mgr2.get_user(user.id).name, user.name)
            self.assertEqual(mgr2.get_recipe(recipe.id).title, recipe.title)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
