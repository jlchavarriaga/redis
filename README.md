# Redis y FastAPI

Este proyecto demuestra cómo utilizar Redis como almacenamiento en caché para acelerar la autenticación de usuarios, junto con PostgreSQL como base de datos principal. La aplicación está construida con FastAPI y Docker para la gestión de los servicios.

## Características
- Registro de usuarios en PostgreSQL.
- Almacenamiento en caché de usuarios en Redis para inicio de sesión rápido.
- Endpoints para registrar y autenticar usuarios.

## Prerrequisitos
- Docker y Docker Compose instalados en tu sistema.
- Python 3.7+ instalado.

## Instalación y Uso
### 1. Clonar el Repositorio
   ```bash
   git clone [https://github.com/tu_usuario/tu_repositorio.git](https://github.com/jlchavarriaga/redis)
   cd redis
   ```
### 2. USO
1. Crear un entorno virtual con: `python -m venv venv`
2. Entrar al entorno con: `venv/scripts/activate`
3. Instalar las dependencias con: `pip install -r requirements.txt`
4. Ejecutar Docker y FastAPI
    Iniciar Docker: Ejecuta el siguiente comando para iniciar los servicios de PostgreSQL y Redis.
    `docker-compose up -d`
5. Ejecutar FastAPI: Ejecuta FastAPI con Uvicorn.
    Ejecutar el proyecto con: `uvicorn main:app --reload`
6. Registro de usuario:
    Envia una solicitud POST a http://localhost:8000/register con un JSON como:
    ```bash
    {
    "username": "testuser",
    "password": "testpass"
    }
    ```

7. Inicio de sesión:
    Envia una solicitud POST a http://localhost:8000/login con el mismo JSON para verificar el inicio de sesión.

# Desarrollo
8. Crear endpoint para eliminar todos los datos de redis
