from pydantic import BaseModel, EmailStr, Field



class RegisterUser(BaseModel):
    """
    Schema for user registration input validation.
    """
    first_name: str = Field(..., example="John",description="First name of the user")
    last_name: str = Field(..., example="Doe",description="Last name of the user")
    email: EmailStr = Field(..., example="john.doe@example.com",description="Email address of the user")
    password: str = Field(..., min_length=8, example="securePassword123",description="Password of the user")

class LoginUser(BaseModel):
    """
    Schema for user login input validation.
    """
    email: EmailStr = Field(..., example="john.doe@example.com",description="Email address of the user")
    password: str = Field(..., min_length=8, example="securePassword123",description="Password of the user")