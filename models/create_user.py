from typing import Optional, List, Any
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler


# Custom ObjectId field for MongoDB
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_obj: core_schema.CoreSchema, handler: GetCoreSchemaHandler) -> dict:
        return {
            "type": "string",
            "examples": ["507f1f77bcf86cd799439011"]
        }


# Basic user model for creation
class User(BaseModel):
    name: str
    email: str
    password: str


# Public user model (returned from API)
class ShowUser(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    email: str


# Login input model
class Login(BaseModel):
    username: str
    password: str


# JWT Token response model
class Token(BaseModel):
    access_token: str
    token_type: str


# Token payload for current user info
class TokenData(BaseModel):
    email: Optional[str] = None