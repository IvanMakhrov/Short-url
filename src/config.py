from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

#DB_USER=os.getenv("DB_USER")
#DB_PASS=os.getenv("DB_PASS")
#DB_HOST=os.getenv("DB_HOST")
#DB_PORT=os.getenv("DB_PORT")
#DB_NAME=os.getenv("DB_NAME")

class Settings(BaseSettings):
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_HOST: str = "db"
    DB_PORT: str = "5432"
    DB_NAME: str = "shortlinks"
    
    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()
