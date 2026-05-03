# gemini_service.py
# Calls Gemini 2.5 Flash and parses the structured JSON recipe response.

import os
import re
import json
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", " api key")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

PROMPT_TEMPLATE = """
You are a professional chef. Given the inputs below, suggest a recipe.

Ingredients: {ingredients}
Target calories: {calories} kcal
Time limit: {time_limit} minutes

Reply with ONLY a valid JSON object — no markdown, no explanation, no code fences.
Use exactly this structure:
{{
  "title": "Recipe Name",
  "ingredients_list": ["item 1", "item 2"],
  "instructions": ["Step 1", "Step 2"],
  "calories": 400,
  "time_limit": 30
}}
"""


def get_recipe(ingredients: str, calories: int, time_limit: int) -> dict:
    """Call Gemini and return a parsed recipe dict."""
    prompt = PROMPT_TEMPLATE.format(
        ingredients=ingredients,
        calories=calories,
        time_limit=time_limit,
    )

    response = model.generate_content(prompt)
    raw = response.text

    # Strip markdown fences if present (```json ... ```)
    raw = re.sub(r"```(?:json)?", "", raw).replace("`", "").strip()

    # Extract the first {...} block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in Gemini response:\n{raw[:300]}")

    data = json.loads(match.group())

    # Basic validation
    required = {"title", "ingredients_list", "instructions", "calories", "time_limit"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Response missing fields: {missing}")

    data["calories"]   = int(data["calories"])
    data["time_limit"] = int(data["time_limit"])

    return data
