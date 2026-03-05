# DHEX — Cooking & Baking System

DHEX is a cooking and baking assistant that lets you register individual bakers and cooks, and manage their recipes.

## Features

- **User management** – register individuals with a name, email, skill level, and dietary preferences
- **Recipe management** – add, view, search, update, and delete baking or cooking recipes
- **Ingredient tracking** – each recipe stores a structured list of ingredients (name, quantity, unit)
- **JSON persistence** – all data is saved to a local JSON file so nothing is lost between sessions
- **CLI interface** – interactive command-line menu for everyday use

## Project structure

```
DHEX/
├── src/
│   ├── models.py          # User, Ingredient, Recipe data models
│   └── recipe_manager.py  # RecipeManager – CRUD for users and recipes
├── tests/
│   └── test_dhex.py       # Unit tests (26 tests)
├── main.py                # Interactive CLI entry point
└── README.md
```

## Requirements

- Python 3.10+

No third-party packages are required to run the application.
`pytest` is needed only to run the tests:

```bash
pip install pytest
```

## Running the CLI

```bash
python main.py
```

By default the data is stored in `dhex_data.json` in the current directory.
You can change the file location with the `DHEX_STORAGE` environment variable:

```bash
DHEX_STORAGE=/path/to/my_data.json python main.py
```

## Running the tests

```bash
python -m pytest tests/ -v
```

## Quick example (programmatic usage)

```python
from src.models import Ingredient, Recipe, RecipeCategory, SkillLevel, User
from src.recipe_manager import RecipeManager

manager = RecipeManager()

# Register a baker
alice = User(name="Alice", email="alice@example.com", skill_level=SkillLevel.INTERMEDIATE)
manager.add_user(alice)

# Add a baking recipe
bread = Recipe(
    title="Sourdough Bread",
    category=RecipeCategory.BAKING,
    ingredients=[
        Ingredient("flour", "500", "grams"),
        Ingredient("water", "350", "ml"),
        Ingredient("salt",  "10",  "grams"),
    ],
    instructions=[
        "Mix flour, water and salt.",
        "Fold the dough every 30 minutes for 4 hours.",
        "Shape, proof overnight, bake at 230 °C for 40 minutes.",
    ],
    author_id=alice.id,
    prep_time_minutes=30,
    cook_time_minutes=40,
    servings=8,
)
manager.add_recipe(bread)

# Search for recipes containing flour
results = manager.search_recipes("flour")
print(results[0].title)  # → Sourdough Bread
```
