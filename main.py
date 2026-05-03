# main.py
# FastAPI backend: hashes inputs, checks SQLite cache, calls Gemini on miss.

import hashlib
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Recipe, get_db, init_db
from gemini_service import get_recipe


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()          # create tables on startup
    yield


app = FastAPI(title="Recipe Suggester", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------- Schemas ----------

class RecipeRequest(BaseModel):
    ingredients: str
    calories:    int
    time_limit:  int

class RecipeResponse(BaseModel):
    title:            str
    ingredients_list: list[str]
    instructions:     list[str]
    calories:         int
    time_limit:       int
    cached:           bool


# ---------- Helper ----------

def make_key(ingredients: str, calories: int, time_limit: int) -> str:
    raw = f"{ingredients.lower().strip()}|{calories}|{time_limit}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------- Endpoint ----------

@app.post("/getrecipe", response_model=RecipeResponse)
def getrecipe(payload: RecipeRequest, db: Session = Depends(get_db)):
    # Validate inputs
    if not payload.ingredients.strip():
        raise HTTPException(status_code=400, detail="Ingredients cannot be empty.")
    if not (50 <= payload.calories <= 5000):
        raise HTTPException(status_code=400, detail="Calories must be between 50 and 5000.")
    if not (5 <= payload.time_limit <= 300):
        raise HTTPException(status_code=400, detail="Time limit must be between 5 and 300 minutes.")

    key = make_key(payload.ingredients, payload.calories, payload.time_limit)

    # --- Cache hit ---
    cached = db.query(Recipe).filter(Recipe.ingredients_key == key).first()
    if cached:
        return RecipeResponse(
            title            = cached.title,
            ingredients_list = json.loads(cached.ingredients_list),
            instructions     = json.loads(cached.instructions),
            calories         = cached.calories,
            time_limit       = cached.time_limit,
            cached           = True,
        )

    # --- Cache miss: call Gemini ---
    try:
        data = get_recipe(payload.ingredients, payload.calories, payload.time_limit)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Gemini error: {e}")

    # --- Save to SQLite ---
    row = Recipe(
        ingredients_key  = key,
        title            = data["title"],
        calories         = data["calories"],
        time_limit       = data["time_limit"],
        ingredients_list = json.dumps(data["ingredients_list"]),
        instructions     = json.dumps(data["instructions"]),
    )
    db.add(row)
    db.commit()

    return RecipeResponse(**data, cached=False)
