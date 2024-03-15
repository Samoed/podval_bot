import json

from database.recipes import Recipes


def parse_recipes(file_path: str) -> list[Recipes]:
    """
    Parses the recipes from the result.json file and returns a dictionary with the recipes.
    """
    with open(file_path) as file:
        recipes = json.load(file)
    messages = [m["text_entities"] for m in recipes["messages"] if len(m["text_entities"]) > 0]
    recipes = []
    for m in messages:
        link, name = None, None
        for e in m:
            if e["type"] == "link":
                link = e["text"]
            if e["type"] == "plain":
                name = e["text"].strip().lower()
        if link and name:
            recipes.append(Recipes(name=name, link=link))
    return recipes
