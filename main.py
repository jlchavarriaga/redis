from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import redis
import os
from dotenv import load_dotenv
from faker import Faker
import time
import concurrent.futures

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

# Faker instance
faker = Faker()

@app.post("/register-1000-users")
def register_1000_users():
    for _ in range(1000):
        username = faker.user_name()
        password = faker.password()

        # Insert user into PostgreSQL
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s) ON CONFLICT DO NOTHING", (username, password))
        conn.commit()

        # Store user in Redis
        redis_client.set(username, password)

    return {"message": "1000 users registered successfully."}

@app.delete("/delete-all-users")
def delete_all_users():
    try:
        # Eliminar todos los datos usando TRUNCATE
        cursor.execute("TRUNCATE TABLE users RESTART IDENTITY;")
        conn.commit()
        return {"message": "All users deleted successfully from PostgreSQL."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear-redis")
def clear_redis():
    redis_client.flushall()
    return {"message": "All data cleared from Redis"}

@app.get("/simulate-logins")
def simulate_logins():
    # Obtener 200 usuarios de la base de datos
    cursor.execute("SELECT username, password FROM users LIMIT 12500")
    users = cursor.fetchall()

    if not users:
        return {"message": "No users found in the database."}

    # Función para simular el inicio de sesión
    def simulate_login(username, password):
        start_time = time.time()
        try:
            # Verificar en Redis primero
            if redis_client.exists(username):
                stored_password = redis_client.get(username).decode('utf-8')
                if stored_password == password:
                    elapsed_time = time.time() - start_time
                    return {"username": username, "status": "success", "time": elapsed_time}
                else:
                    return {"username": username, "status": "failure", "time": time.time() - start_time}

            # Verificar en PostgreSQL si no se encuentra en Redis
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user_in_db = cursor.fetchone()

            if user_in_db:
                # Almacenar en Redis para futuros inicios de sesión
                redis_client.set(username, password)
                elapsed_time = time.time() - start_time
                return {"username": username, "status": "success", "time": elapsed_time}
            else:
                return {"username": username, "status": "failure", "time": time.time() - start_time}
        except Exception as e:
            return {"username": username, "status": "error", "error": str(e), "time": time.time() - start_time}

    # Ejecutar los inicios de sesión de manera concurrente
    successful_logins = 0
    failed_logins = 0
    total_time = 0.0
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(simulate_login, username, password) for username, password in users]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            total_time += result["time"]  # Sumar el tiempo de cada inicio de sesión
            if result["status"] == "success":
                successful_logins += 1
                print(f"Login successful for {result['username']} in {result['time']:.4f} seconds")
            else:
                failed_logins += 1
                print(f"Login failed for {result['username']} in {result['time']:.4f} seconds")

    # Calcular el promedio de tiempo total
    average_time = total_time / len(users) if len(users) > 0 else 0.0

    return {
        "total_logins": len(users),
        "successful_logins": successful_logins,
        "failed_logins": failed_logins,
        "average_time_seconds": average_time,
        "results": results
    }