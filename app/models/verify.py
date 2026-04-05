from pydantic import BaseModel

class VerifyModel(BaseModel):
    return_code: int
    stdout: None | str
    stderr: None | str