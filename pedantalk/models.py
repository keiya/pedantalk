from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    HOST = "host"
    GUEST = "guest"


class Speaker(BaseModel):
    role: Role
    voice: str
    name: str
    personality: str
    background: str
    voice_instruction: Optional[str] = None


class Topic(BaseModel):
    title: str
    description: str
    keywords: List[str] = Field(default_factory=list)


class DialogueTurn(BaseModel):
    speaker: Role
    text: str


class Conversation(BaseModel):
    topic: Topic
    host: Speaker
    guest: Speaker
    turns: List[DialogueTurn] = Field(default_factory=list)


class AudioSegment(BaseModel):
    speaker: Role
    text: str
    audio_path: str
    duration_ms: int


class PodcastEpisode(BaseModel):
    topic: Topic
    host: Speaker
    guest: Speaker
    conversation: List[DialogueTurn]
    audio_segments: List[AudioSegment] = Field(default_factory=list)
    final_audio_path: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict) 
