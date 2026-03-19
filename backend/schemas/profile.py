from pydantic import BaseModel

class ProfileInput(BaseModel):
    url: str
