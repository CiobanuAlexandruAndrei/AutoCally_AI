# .env

Create a .env file in the root directory and add the following variables:
```
DB_USER=
DB_PASSWORD= 
DB_HOST=
DB_PORT=
DB_NAME=autocally

GROQ_API_KEY=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
CARTESIA_API_KEY=sk_car_J30BYq5bkyWK_3vGd16Kt
DEEPGRAM_API_KEY=d430dfd320703fc5125e77084d6653423aa05783

```

# Run
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

flask db init
flask db migrate -m "Initial migration."
flask db upgrade

python run.py
```
