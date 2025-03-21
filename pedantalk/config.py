import os
import random
from typing import Dict, List, Optional

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration settings for the pedantalk application."""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    
    # Available voices
    AVAILABLE_VOICES: List[str] = [
        "alloy", "ash", "ballad", "coral", "echo", 
        "fable", "onyx", "nova", "sage", "shimmer"
    ]
    
    # Voice settings
    HOST_VOICE: str = os.getenv("HOST_VOICE", "nova")
    HOST_VOICE_INSTRUCTION: str = os.getenv("HOST_VOICE_INSTRUCTION", "")
    
    # Guest voice - will be determined at runtime
    @staticmethod
    def _select_random_guest_voice() -> str:
        """Select a random guest voice different from the host voice."""
        default_host = "echo"
        host_voice = os.getenv("HOST_VOICE", default_host)
        guest_voice_env = os.getenv("GUEST_VOICE")
        
        if guest_voice_env:
            return guest_voice_env
        
        available_voices = ["alloy", "ash", "ballad", "coral", "echo", 
                            "fable", "onyx", "nova", "sage", "shimmer"]
        available = [v for v in available_voices if v != host_voice]
        return random.choice(available)
    
    GUEST_VOICE: str = _select_random_guest_voice()
    
    # Audio settings
    SILENCE_MIN_MS: int = int(os.getenv("SILENCE_MIN_MS", "500"))
    SILENCE_MAX_MS: int = int(os.getenv("SILENCE_MAX_MS", "1500"))
    
    # Output directories
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    AUDIO_DIR: str = os.path.join(OUTPUT_DIR, "audio")
    TRANSCRIPT_DIR: str = os.path.join(OUTPUT_DIR, "transcripts")
    
    @classmethod
    def validate(cls) -> Optional[str]:
        """
        Validate the configuration.
        
        Returns:
            Optional[str]: Error message if validation fails, None otherwise.
        """
        if not cls.OPENAI_API_KEY:
            return "OPENAI_API_KEY is required but not set"
        
        if cls.SILENCE_MIN_MS >= cls.SILENCE_MAX_MS:
            return "SILENCE_MIN_MS must be less than SILENCE_MAX_MS"
        
        if cls.HOST_VOICE not in cls.AVAILABLE_VOICES:
            return f"HOST_VOICE must be one of {', '.join(cls.AVAILABLE_VOICES)}"
        
        return None
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary output directories if they don't exist."""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.AUDIO_DIR, exist_ok=True)
        os.makedirs(cls.TRANSCRIPT_DIR, exist_ok=True)
    
    @classmethod
    def to_dict(cls) -> Dict[str, str]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, str]: Dictionary of configuration values.
        """
        return {
            "MODEL_NAME": cls.MODEL_NAME,
            "HOST_VOICE": cls.HOST_VOICE,
            "HOST_VOICE_INSTRUCTION": cls.HOST_VOICE_INSTRUCTION,
            "GUEST_VOICE": cls.GUEST_VOICE,
            "SILENCE_MIN_MS": str(cls.SILENCE_MIN_MS),
            "SILENCE_MAX_MS": str(cls.SILENCE_MAX_MS),
        } 
