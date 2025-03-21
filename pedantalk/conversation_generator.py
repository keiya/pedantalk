from typing import Any, Dict, List, Optional
import json
import random

from openai import OpenAI

from pedantalk.config import Config
from pedantalk.models import Conversation, DialogueTurn, Role, Speaker, Topic


class ConversationGenerator:
    """Generator for podcast conversations using OpenAI."""
    
    def __init__(self) -> None:
        """Initialize the conversation generator with OpenAI client."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def _generate_host(self, topic: Topic) -> Speaker:
        """
        Generate the host character.
        
        Args:
            topic: The podcast topic.
            
        Returns:
            Speaker: The host speaker object.
        """
        return Speaker(
            role=Role.HOST,
            voice=Config.HOST_VOICE,
            name="Alex Morgan",
            personality="Curious, intellectually engaged, and thoughtful. Asks probing questions but admits knowledge limitations.",
            background="Liberal arts background with broad general knowledge but limited specialized expertise.",
            voice_instruction=Config.HOST_VOICE_INSTRUCTION if Config.HOST_VOICE_INSTRUCTION else None
        )
    
    def _generate_guest_voice_instruction(self, personality: str, background: str) -> str:
        """
        Generate a voice instruction for the guest based on their personality and background.
        
        Args:
            personality: The guest's personality description.
            background: The guest's background description.
            
        Returns:
            str: A voice instruction for the guest.
        """
        prompt = (
            f"Based on the following personality and background, create a voice instruction for a text-to-speech "
            f"system that would best convey this person's speaking style:\n\n"
            f"Personality: {personality}\n"
            f"Background: {background}\n\n"
            f"This should be a concise instruction describing how the voice should sound, such as tone, pace, "
            f"emotion, accent, etc. Keep it under 100 characters."
        )
        
        response = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a voice direction expert for audiobooks and podcasts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        
        content = response.choices[0].message.content
        return content.strip() if content else "Speak with authority and clarity."
    
    def _generate_guest(self, topic: Topic) -> Speaker:
        """
        Generate the guest expert based on the topic.
        
        Args:
            topic: The podcast topic.
            
        Returns:
            Speaker: The guest speaker object.
        """
        prompt = (
            f"Create an expert guest for a podcast on the topic: '{topic.title}'\n\n"
            f"The topic is about: {topic.description}\n\n"
            "Generate a JSON response with the following structure:\n"
            "{\n"
            "  \"name\": \"Full Name\",\n"
            "  \"personality\": \"Brief personality description\",\n"
            "  \"background\": \"Professional background and expertise relevant to the topic\"\n"
            "}"
        )
        
        response = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert at creating realistic podcast guest personas."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            try:
                guest_data: Dict[str, str] = json.loads(content)
                personality = guest_data["personality"]
                background = guest_data["background"]
                voice_instruction = self._generate_guest_voice_instruction(personality, background)
                
                return Speaker(
                    role=Role.GUEST,
                    voice=Config.GUEST_VOICE,
                    name=guest_data["name"],
                    personality=personality,
                    background=background,
                    voice_instruction=voice_instruction
                )
            except (KeyError, ValueError):
                pass
        
        # Fallback guest if generation fails
        return Speaker(
            role=Role.GUEST,
            voice=Config.GUEST_VOICE,
            name="Dr. Jamie Reynolds",
            personality="Articulate, thoughtful, and passionate about their field of expertise.",
            background=f"Leading researcher and author in the field of {topic.keywords[0] if topic.keywords else topic.title}",
            voice_instruction="Speak with authority and academic precision."
        )
    
    def _generate_conversation_turns(self, topic: Topic, host: Speaker, guest: Speaker, num_turns: int = 10) -> List[DialogueTurn]:
        """
        Generate the conversation between host and guest.
        
        Args:
            topic: The podcast topic.
            host: The host speaker.
            guest: The guest speaker.
            num_turns: Number of conversation turns to generate.
            
        Returns:
            List[DialogueTurn]: List of dialogue turns in the conversation.
        """
        # Adjust for the 3 outro turns we'll add later
        main_conversation_turns = max(3, num_turns - 3)
        
        system_prompt = (
            f"You are generating a podcast conversation between a host ({host.name}) and "
            f"a guest expert ({guest.name}) on the topic: '{topic.title}'.\n\n"
            f"Host personality: {host.personality}\n"
            f"Host background: {host.background}\n\n"
            f"Guest personality: {guest.personality}\n"
            f"Guest background: {guest.background}\n\n"
            "Generate a natural, engaging, and SUBSTANTIVE conversation with real content, not just an introduction and conclusion. "
            "The host should ask thoughtful questions, and the guest should provide detailed expert insights. "
            "The conversation must be intellectually stimulating and have significant depth and substance. "
            "DO NOT generate generic or superficial content. Include specific details, examples, and nuanced perspectives."
            "DO NOT include any wrap-up or conclusion - I will add those separately."
        )
        
        user_prompt = (
            f"Create a substantive intellectual podcast conversation on '{topic.title}' with EXACTLY {main_conversation_turns} turns. "
            "The conversation MUST alternate between host and guest, starting with the host.\n\n"
            "Essential requirements:\n"
            f"1. A brief welcoming introduction from the host (first turn only)\n"
            f"2. At least {main_conversation_turns-1} substantive exchanges with real intellectual content\n"
            "3. Specific questions that explore different aspects of the topic in depth\n"
            "4. Detailed, informative responses from the guest with examples and nuance\n"
            "5. The conversation must progress logically with follow-up questions\n\n"
            "Format your response as a JSON array with each element having exactly two fields: 'speaker' (either 'host' or 'guest') and 'text':\n\n"
            "[\n"
            "  {\n"
            "    \"speaker\": \"host\",\n"
            "    \"text\": \"Welcome to our podcast...\"\n"
            "  },\n"
            "  {\n"
            "    \"speaker\": \"guest\",\n"
            "    \"text\": \"Thank you for having me...\"\n"
            "  },\n"
            f"  // IMPORTANT: You must generate {main_conversation_turns-2} MORE turns with substantial content\n"
            "]\n\n"
            "DO NOT include any conclusion or wrap-up turns - those will be added separately.\n"
            f"ENSURE exactly {main_conversation_turns} turns total."
        )
        
        response = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        turns: List[DialogueTurn] = []
        
        if content:
            try:
                # Debug the received content
                print(f"Debug - API response content: {content[:300]}...")
                
                # Parse JSON response
                json_data = json.loads(content)
                
                # Handle different response formats
                turns_data = None
                if isinstance(json_data, list):
                    turns_data = json_data
                elif isinstance(json_data, dict) and any(k in json_data for k in ['conversation', 'turns', 'messages', 'dialogues']):
                    for key in ['conversation', 'turns', 'messages', 'dialogues']:
                        if key in json_data and isinstance(json_data[key], list):
                            turns_data = json_data[key]
                            print(f"Found turns in field: {key}")
                            break
                
                # If we still don't have turns data, look for any list field
                if turns_data is None and isinstance(json_data, dict):
                    for key, value in json_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            turns_data = value
                            print(f"Using list field: {key}")
                            break
                
                # Process turns if we found them
                if turns_data and isinstance(turns_data, list):
                    print(f"Processing {len(turns_data)} conversation turns")
                    for i, turn_data in enumerate(turns_data):
                        if isinstance(turn_data, dict):
                            speaker_key = next((k for k in turn_data.keys() if k.lower() == 'speaker'), 'speaker')
                            text_key = next((k for k in turn_data.keys() if k.lower() == 'text'), 'text')
                            
                            speaker_value = turn_data.get(speaker_key, "")
                            text_value = turn_data.get(text_key, "")
                            
                            role = Role.HOST if str(speaker_value).lower() == "host" else Role.GUEST
                            turns.append(DialogueTurn(speaker=role, text=str(text_value)))
                        else:
                            print(f"Warning: Turn {i} is not a dictionary: {turn_data}")
                else:
                    raise ValueError(f"No valid turns data found in response: {json_data}")
                    
                # Check if we have enough turns
                expected_min_turns = max(5, main_conversation_turns - 2)  # Allow slight flexibility but ensure substance
                if len(turns) < expected_min_turns:
                    print(f"WARNING: Only {len(turns)} turns generated. Expected at least {expected_min_turns} (requested: {main_conversation_turns})")
                    
                    # If too few turns, add fallback conversation content
                    if len(turns) <= 2:  # If only intro turns or less
                        print("Critical: Generated conversation is too short - using fallback content")
                        # Keep any existing turns (usually intro)
                        existing_turns = turns.copy() if turns else []
                        turns = [
                            DialogueTurn(speaker=Role.HOST, text=f"Welcome to Pedantalk. Today we're discussing {topic.title}. I'm joined by {guest.name}, an expert in this field."),
                            DialogueTurn(speaker=Role.GUEST, text=f"Thanks for having me, {host.name}. It's a pleasure to be here to talk about this fascinating topic.")
                        ]
                        
                        # Only use existing turns if we have none yet (avoid duplication)
                        if not existing_turns:
                            turns = existing_turns
                    
                    # Add substantive Q&A content until we reach minimum length
                    current_speaker = Role.HOST if turns[-1].speaker == Role.GUEST else Role.GUEST
                    while len(turns) < expected_min_turns:
                        if current_speaker == Role.HOST:
                            turns.append(DialogueTurn(
                                speaker=Role.HOST,
                                text=f"One important aspect of {topic.title} that we haven't discussed yet is the broader implications. Could you elaborate on how this affects society at large?"
                            ))
                        else:
                            turns.append(DialogueTurn(
                                speaker=Role.GUEST,
                                text=f"That's an excellent question. When we consider {topic.title}, we have to recognize that it impacts multiple domains of human experience. Research has shown several key patterns. First, there's the immediate effect on individuals and communities. Second, we see longer-term structural changes that reshape institutions. Finally, there are ethical considerations that we must address carefully."
                            ))
                        current_speaker = Role.HOST if current_speaker == Role.GUEST else Role.GUEST
                
                # Print final turn count for debugging
                print(f"Final conversation turn count: {len(turns)} (before adding outro)")
            
            except (KeyError, ValueError, AttributeError, json.JSONDecodeError) as e:
                print(f"Error parsing conversation turns: {e}")
                # Fallback to default conversation
                turns = [
                    DialogueTurn(speaker=Role.HOST, text=f"Welcome to Pedantalk. Today we're discussing {topic.title}. I'm joined by {guest.name}, an expert in this field."),
                    DialogueTurn(speaker=Role.GUEST, text=f"Thanks for having me, {host.name}. It's a pleasure to be here to talk about this fascinating topic.")
                ]
        
        # Add structured outro (3 turns)
        # 1. Host wraps up and asks for final thoughts
        turns.append(DialogueTurn(
            speaker=Role.HOST,
            text=f"We're approaching the end of our time. {guest.name}, I'd like to thank you for this fascinating discussion on {topic.title}. Before we wrap up, what are your final thoughts on this topic?"
        ))
        
        # 2. Guest shares final thoughts
        turns.append(DialogueTurn(
            speaker=Role.GUEST,
            text=f"Thank you for having me, {host.name}. To summarize my thoughts on {topic.title}, I believe it's a critically important area that will continue to evolve. I've enjoyed our conversation and hope your listeners found it insightful."
        ))
        
        # 3. Host concludes the episode
        turns.append(DialogueTurn(
            speaker=Role.HOST,
            text=f"Thank you, {guest.name}, for sharing your expertise with us today. To our listeners, thank you for joining us for another episode of Pedantalk. Please join us next time for more thought-provoking discussions. Until then, keep questioning and stay curious."
        ))
        
        return turns
    
    def generate_conversation(self, topic: Topic, num_turns: int = 10) -> Conversation:
        """
        Generate a complete podcast conversation.
        
        Args:
            topic: The podcast topic.
            num_turns: Number of conversation turns to generate (including the structured outro).
            
        Returns:
            Conversation: The complete conversation object.
        """
        host = self._generate_host(topic)
        guest = self._generate_guest(topic)
        turns = self._generate_conversation_turns(topic, host, guest, num_turns)
        
        return Conversation(
            topic=topic,
            host=host,
            guest=guest,
            turns=turns
        ) 
