from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class UserChangePassword(BaseModel):
    email: EmailStr
    password: str
    newPassword: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
