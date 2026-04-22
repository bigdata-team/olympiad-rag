from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    workspace_id: str
    user_id: str
    files: list[str] | None = None
    messages: list[Message]
    top_p: float = 1.0
    top_k: int = 0
    temperature: float = 1.0
    stream: bool = False


class ChatChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class ChatResponse(BaseModel):
    id: str
    object: str
    choices: list[ChatChoice]
