import logging
import os
from datetime import datetime
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlmodel import Field, SQLModel, create_engine

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)


def _parse_azure_postgres_connection_string(raw_connection_string: str) -> dict[str, str]:
    """Parse connection strings from either azd or portal formats.

    Supported formats:
    - Space-delimited: "dbname=... host=... port=... sslmode=... user=... password=..."
    - Semicolon-delimited: "Database=...;Server=...;User Id=...;Password=..."
    """
    details: dict[str, str] = {}

    if ";" in raw_connection_string:
        # Azure portal style connection string.
        parts = [part.strip() for part in raw_connection_string.split(";") if part.strip()]
        for part in parts:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            normalized_key = key.strip().lower().replace(" ", "")
            details[normalized_key] = value.strip()

        return {
            "dbname": details.get("database", ""),
            "host": details.get("server", ""),
            "port": details.get("port", "5432"),
            "sslmode": details.get("sslmode", "require"),
            "user": details.get("userid", details.get("user", "")),
            "password": details.get("password", ""),
        }

    # azd style connection string.
    parts = [part.strip() for part in raw_connection_string.split() if part.strip()]
    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        details[key.strip().lower()] = value.strip()

    return {
        "dbname": details.get("dbname", ""),
        "host": details.get("host", ""),
        "port": details.get("port", "5432"),
        "sslmode": details.get("sslmode", "require"),
        "user": details.get("user", ""),
        "password": details.get("password", ""),
    }

sql_url = ""
if os.getenv("WEBSITE_HOSTNAME"):
    logger.info("Connecting to Azure PostgreSQL Flexible server based on AZURE_POSTGRESQL_CONNECTIONSTRING...")
    env_connection_string = os.getenv("AZURE_POSTGRESQL_CONNECTIONSTRING")
    if env_connection_string is None:
        logger.info("Missing environment variable AZURE_POSTGRESQL_CONNECTIONSTRING")
    else:
        details = _parse_azure_postgres_connection_string(env_connection_string)

        # Properly format the URL for SQLAlchemy
        sql_url = (
            f"postgresql://{quote_plus(details['user'])}:{quote_plus(details['password'])}"
            f"@{details['host']}:{details['port']}/{details['dbname']}?sslmode={details['sslmode']}"
        )

else:
    logger.info("Connecting to local PostgreSQL server based on .env file...")
    load_dotenv()
    POSTGRES_USERNAME = os.environ.get("DBUSER")
    POSTGRES_PASSWORD = os.environ.get("DBPASS")
    POSTGRES_HOST = os.environ.get("DBHOST")
    POSTGRES_DATABASE = os.environ.get("DBNAME")
    POSTGRES_PORT = os.environ.get("DBPORT", 5432)

    sql_url = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"

engine = create_engine(sql_url)


def create_db_and_tables():
    return SQLModel.metadata.create_all(engine)

class Restaurant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    street_address: str = Field(max_length=50)
    description: str = Field(max_length=250)

    def __str__(self):
        return f"{self.name}"

class Review(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    restaurant: int = Field(foreign_key="restaurant.id")
    user_name: str = Field(max_length=50)
    rating: int | None
    review_text: str = Field(max_length=500)
    review_date: datetime

    def __str__(self):
        return f"{self.name}"
