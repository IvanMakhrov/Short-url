from fastapi_users import schemas


class UserRead(schemas.BaseUser):
    id: int
    email: str


class UserCreate(schemas.BaseUserCreate):
    email: str
    password: str
