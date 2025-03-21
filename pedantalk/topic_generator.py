from typing import List
import json

import openai
from openai import OpenAI

from pedantalk.config import Config
from pedantalk.models import Topic


class TopicGenerator:
    """Generator for podcast topics using OpenAI."""
    
    def __init__(self) -> None:
        """Initialize the topic generator with OpenAI client."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def generate_topic(self) -> Topic:
        """
        Generate a random podcast topic.
        
        Returns:
            Topic: A generated topic with title, description and keywords.
        """
        response = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a podcast topic generator. Generate an interesting topic for "
                        "an intellectual discussion podcast. The topic should be thought-provoking "
                        "and suitable for a 20-30 minute conversation between a curious host and "
                        "an expert guest."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Generate a podcast topic with the following JSON structure:\n"
                        "{\n"
                        "  \"title\": \"Topic title\",\n"
                        "  \"description\": \"A paragraph describing the topic\",\n"
                        "  \"keywords\": [\"keyword1\", \"keyword2\", \"keyword3\"]\n"
                        "}"
                    )
                }
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            topic_dict = json.loads(content)
            return Topic(
                title=topic_dict["title"],
                description=topic_dict["description"],
                keywords=topic_dict["keywords"]
            )
        
        # Fallback topic if generation fails
        return Topic(
            title="The Future of Artificial Intelligence",
            description="Exploring the ethical implications and potential developments of AI in the next decade.",
            keywords=["AI ethics", "future technology", "machine learning"]
        ) 
