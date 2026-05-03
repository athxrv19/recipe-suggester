# 1. Install
pip install -r requirements.txt

# 2. (Optional) set your API key — the key is already hardcoded as a fallback
GEMINI_API_KEY="Your API Key"
DATABASE_URL="mysql+pymysql://root:your_password@localhost/recipes_db"

# 3. Start the backend (creates recipes.db automatically)
uvicorn main:app --reload

# 4. Start the frontend (new terminal)
streamlit run app.py
