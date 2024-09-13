from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# FastAPI app
app = FastAPI()

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    db=int(os.getenv('REDIS_DB'))
)

# PostgreSQL connection
conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT')
)
cursor = conn.cursor()

# Pydantic model for user
class User(BaseModel):
    username: str
    password: str

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL
)
""")
conn.commit()

@app.post("/register")
def register_user(user: User):
    # Check if user is in Redis
    if redis_client.exists(user.username):
        return {"message": "User already exists in Redis"}

    # Check if user exists in PostgreSQL
    cursor.execute("SELECT * FROM users WHERE username = %s", (user.username,))
    user_in_db = cursor.fetchone()

    if user_in_db:
        # Store user in Redis for future logins
        redis_client.set(user.username, user.password)
        return {"message": "User already exists in PostgreSQL. Now stored in Redis."}

    # Insert user into PostgreSQL
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, user.password))
    conn.commit()

    # Store user in Redis
    redis_client.set(user.username, user.password)

    return {"message": "User registered successfully and stored in Redis."}

@app.post("/login")
def login_user(user: User):
    # Check in Redis first
    if redis_client.exists(user.username):
        stored_password = redis_client.get(user.username).decode('utf-8')
        if stored_password == user.password:
            return {"message": "User authenticated successfully using Redis."}
        else:
            raise HTTPException(status_code=401, detail="Incorrect password.")

    # Check in PostgreSQL if not found in Redis
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (user.username, user.password))
    user_in_db = cursor.fetchone()

    if user_in_db:
        # Store user in Redis for future logins
        redis_client.set(user.username, user.password)
        return {"message": "User authenticated successfully using PostgreSQL and stored in Redis."}

    raise HTTPException(status_code=401, detail="User not found.")
