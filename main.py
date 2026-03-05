"""Interactive CLI for the DHEX cooking and baking system."""

import sys
import os

from src.models import Ingredient, Recipe, RecipeCategory, SkillLevel, User
from src.recipe_manager import RecipeManager

STORAGE_FILE = "dhex_data.json"


def prompt(label: str, required: bool = True) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value or not required:
            return value
        print("  This field is required.")


def print_separator():
    print("-" * 50)


# ------------------------------------------------------------------
# User flows
# ------------------------------------------------------------------

def register_user(manager: RecipeManager) -> None:
    print("\n=== Register User ===")
    name = prompt("Full name")
    email = prompt("Email address")
    print("Skill levels: beginner, intermediate, advanced")
    raw_skill = prompt("Skill level (default: beginner)", required=False) or "beginner"
    try:
        skill = SkillLevel(raw_skill.lower())
    except ValueError:
        print(f"  Unknown skill level '{raw_skill}', defaulting to beginner.")
        skill = SkillLevel.BEGINNER
    raw_prefs = prompt("Dietary preferences (comma-separated, or leave blank)", required=False)
    prefs = [p.strip() for p in raw_prefs.split(",") if p.strip()] if raw_prefs else []
    user = User(name=name, email=email, skill_level=skill, dietary_preferences=prefs)
    try:
        manager.add_user(user)
        print(f"\n✓ User '{name}' registered. ID: {user.id}")
    except ValueError as exc:
        print(f"\n✗ {exc}")


def list_users(manager: RecipeManager) -> None:
    users = manager.list_users()
    if not users:
        print("\nNo users registered yet.")
        return
    print(f"\n{'ID':<38} {'Name':<20} {'Skill':<14} Email")
    print_separator()
    for u in users:
        print(f"{u.id:<38} {u.name:<20} {u.skill_level.value:<14} {u.email}")


# ------------------------------------------------------------------
# Recipe flows
# ------------------------------------------------------------------

def _collect_ingredients() -> list:
    ingredients = []
    print("  Enter ingredients one by one. Leave name blank to stop.")
    while True:
        name = prompt("    Ingredient name", required=False)
        if not name:
            break
        quantity = prompt("    Quantity (e.g. 2, 1.5)")
        unit = prompt("    Unit (e.g. cups, grams; leave blank if none)", required=False)
        ingredients.append(Ingredient(name=name, quantity=quantity, unit=unit or None))
    return ingredients


def _collect_instructions() -> list:
    instructions = []
    print("  Enter instructions one step at a time. Leave blank to stop.")
    step = 1
    while True:
        instruction = prompt(f"    Step {step}", required=False)
        if not instruction:
            break
        instructions.append(instruction)
        step += 1
    return instructions


def add_recipe(manager: RecipeManager) -> None:
    users = manager.list_users()
    if not users:
        print("\nNo users registered. Please register a user first.")
        return
    print("\n=== Add Recipe ===")
    print("Registered users:")
    for u in users:
        print(f"  [{u.id}] {u.name}")
    author_id = prompt("Author ID")
    if not manager.get_user(author_id):
        print("  User not found.")
        return
    title = prompt("Recipe title")
    print("Categories: baking, cooking")
    raw_cat = prompt("Category")
    try:
        category = RecipeCategory(raw_cat.lower())
    except ValueError:
        print(f"  Unknown category '{raw_cat}'.")
        return
    prep = prompt("Prep time (minutes)", required=False) or "0"
    cook = prompt("Cook time (minutes)", required=False) or "0"
    servings = prompt("Servings", required=False) or "1"
    print("Ingredients:")
    ingredients = _collect_ingredients()
    if not ingredients:
        print("  At least one ingredient is required.")
        return
    print("Instructions:")
    instructions = _collect_instructions()
    if not instructions:
        print("  At least one instruction step is required.")
        return
    notes = prompt("Notes (optional)", required=False)
    try:
        recipe = Recipe(
            title=title,
            category=category,
            ingredients=ingredients,
            instructions=instructions,
            author_id=author_id,
            prep_time_minutes=int(prep),
            cook_time_minutes=int(cook),
            servings=int(servings),
            notes=notes or None,
        )
        manager.add_recipe(recipe)
        print(f"\n✓ Recipe '{title}' added. ID: {recipe.id}")
    except ValueError as exc:
        print(f"\n✗ {exc}")


def list_recipes(manager: RecipeManager) -> None:
    print("\n=== List Recipes ===")
    print("Filter by category? (baking / cooking / leave blank for all)")
    raw_cat = prompt("Category filter", required=False)
    category = None
    if raw_cat:
        try:
            category = RecipeCategory(raw_cat.lower())
        except ValueError:
            print(f"  Unknown category '{raw_cat}', showing all.")
    recipes = manager.list_recipes(category=category)
    if not recipes:
        print("No recipes found.")
        return
    print(f"\n{'ID':<38} {'Title':<25} {'Category':<10} {'Total time':<12} Servings")
    print_separator()
    for r in recipes:
        print(
            f"{r.id:<38} {r.title:<25} {r.category.value:<10} "
            f"{r.total_time_minutes} min        {r.servings}"
        )


def view_recipe(manager: RecipeManager) -> None:
    recipe_id = prompt("\nRecipe ID to view")
    recipe = manager.get_recipe(recipe_id)
    if not recipe:
        print("  Recipe not found.")
        return
    author = manager.get_user(recipe.author_id)
    author_name = author.name if author else recipe.author_id
    print(f"\n{'='*50}")
    print(f"  {recipe.title.upper()}")
    print(f"{'='*50}")
    print(f"  Category  : {recipe.category.value}")
    print(f"  Author    : {author_name}")
    print(f"  Prep time : {recipe.prep_time_minutes} min")
    print(f"  Cook time : {recipe.cook_time_minutes} min")
    print(f"  Servings  : {recipe.servings}")
    if recipe.notes:
        print(f"  Notes     : {recipe.notes}")
    print("\nIngredients:")
    for ing in recipe.ingredients:
        print(f"  - {ing}")
    print("\nInstructions:")
    for idx, step in enumerate(recipe.instructions, 1):
        print(f"  {idx}. {step}")
    print()


def search_recipes(manager: RecipeManager) -> None:
    keyword = prompt("\nSearch keyword")
    results = manager.search_recipes(keyword)
    if not results:
        print("  No recipes matched your search.")
        return
    print(f"\nFound {len(results)} recipe(s):")
    for r in results:
        print(f"  [{r.id}] {r.title} ({r.category.value})")


def delete_recipe(manager: RecipeManager) -> None:
    recipe_id = prompt("\nRecipe ID to delete")
    try:
        manager.delete_recipe(recipe_id)
        print("  Recipe deleted.")
    except ValueError as exc:
        print(f"  ✗ {exc}")


# ------------------------------------------------------------------
# Main menu
# ------------------------------------------------------------------

MENU = """
============================
 DHEX — Cooking & Baking
============================
 1. Register user
 2. List users
 3. Add recipe
 4. List recipes
 5. View recipe
 6. Search recipes
 7. Delete recipe
 0. Exit
----------------------------
"""


def main() -> None:
    storage = os.environ.get("DHEX_STORAGE", STORAGE_FILE)
    manager = RecipeManager(storage_path=storage)
    while True:
        print(MENU)
        choice = prompt("Select option").strip()
        if choice == "1":
            register_user(manager)
        elif choice == "2":
            list_users(manager)
        elif choice == "3":
            add_recipe(manager)
        elif choice == "4":
            list_recipes(manager)
        elif choice == "5":
            view_recipe(manager)
        elif choice == "6":
            search_recipes(manager)
        elif choice == "7":
            delete_recipe(manager)
        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("  Invalid option, please try again.")


if __name__ == "__main__":
    main()
