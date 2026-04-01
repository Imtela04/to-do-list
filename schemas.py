#pydantic models to validate and serialise data for request and response 
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    # email: str
    password: str
class TaskCreate(BaseModel):
    title: str
    completed: bool = False
class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    owner_id: int

    class Config:
        from_attributes = True