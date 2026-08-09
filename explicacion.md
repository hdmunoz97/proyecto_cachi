# Sistema - Control de Jornada y Tecnoestrés

Este es un sistema web desarrollado en Django para registrar los turnos de los mecánicos, calcular sus horas trabajadas de forma automática y alertar a la jefatura sobre posibles casos de sobrecarga laboral o tecnoestrés a través de un panel de control con semáforos de riesgo.

---

## Requisitos Previos

Para poder ejecutar este proyecto en tu computadora, necesitas tener instalado lo siguiente:
* **Python** (versión 3.9 o superior)
* **PostgreSQL** (para la base de datos)
* **Git** (para descargar el código)

---

## ¿Cómo levantar el proyecto por primera vez?

### 1. Clonar el repositorio
Descarga el código desde GitHub y entra a la carpeta del proyecto:
```bash
git clone https://github.com/hdmunoz97/proyecto_cachi.git
cd proyecto_cachi


2. Crear y activar el entorno virtual
Bash
python -m venv venv
3. Activar en Windows
Bash
venv\Scripts\activate
4. Instalar las dependencias
Bash
pip install -r requirements.txt
5. Configurar las variables de entorno
Crea un archivo llamado exactamente .env en la carpeta principal del proyecto (donde está manage.py) y agrega tus datos de conexión a PostgreSQL:

Plaintext
SECRET_KEY=tu_clave_secreta_aqui
DB_NAME=nombre_de_tu_base_de_datos
DB_USER=tu_usuario_de_postgres
DB_PASSWORD=tu_contraseña_de_postgres
DB_HOST=localhost
DB_PORT=5432
6. Preparando la base de datos
Bash
python manage.py migrate
7. Levantar el servidor
Bash
python manage.py runserver