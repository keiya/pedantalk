import argparse
import datetime
import logging
import os
from typing import Optional

from openai import OpenAI

from pedantalk.audio_processor import AudioProcessor
from pedantalk.config import Config
from pedantalk.conversation_generator import ConversationGenerator
from pedantalk.models import Conversation, Role, Topic
from pedantalk.topic_generator import TopicGenerator


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(Config.OUTPUT_DIR, "pedantalk.log"))
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate AI podcast episodes")
    parser.add_argument(
        "--topic", 
        type=str, 
        help="Specify a topic instead of generating one"
    )
    parser.add_argument(
        "--turns", 
        type=int, 
        default=20, 
        help="Number of conversation turns (default: 20)"
    )
    parser.add_argument(
        "--host-voice",
        type=str,
        choices=Config.AVAILABLE_VOICES,
        help=f"Voice for the host (one of: {', '.join(Config.AVAILABLE_VOICES)})"
    )
    parser.add_argument(
        "--host-voice-instruction",
        type=str,
        help="Instruction for the host's voice (e.g., 'Speak with a calm, engaging tone')"
    )
    return parser.parse_args()


def generate_episode_id() -> str:
    """Generate a unique episode ID based on timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"episode_{timestamp}"


def create_topic_from_string(topic_str: str) -> Topic:
    """
    Create a Topic object from a string.
    
    Args:
        topic_str: The topic string.
        
    Returns:
        Topic: The created Topic object.
    """
    return Topic(
        title=topic_str,
        description=f"Exploring {topic_str} in depth.",
        keywords=[topic_str.lower()]
    )


def main() -> None:
    """Main entry point for the application."""
    # Set up logging and ensure directories exist
    Config.ensure_directories()
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Parse command line arguments
    args = parse_args()
    
    # Override voice settings if provided via CLI
    if args.host_voice:
        Config.HOST_VOICE = args.host_voice
    
    if args.host_voice_instruction:
        Config.HOST_VOICE_INSTRUCTION = args.host_voice_instruction
        logger.info(f"Using custom host voice instruction: {Config.HOST_VOICE_INSTRUCTION}")
    
    # Validate configuration
    error = Config.validate()
    if error:
        logger.error(f"Configuration error: {error}")
        return
    
    logger.info("Starting pedantalk podcast generation")
    logger.info(f"Using host voice: {Config.HOST_VOICE}")
    logger.info(f"Using guest voice: {Config.GUEST_VOICE}")
    
    # Initialize the OpenAI client
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    # Generate or use provided topic
    if args.topic:
        logger.info(f"Using provided topic: {args.topic}")
        topic = create_topic_from_string(args.topic)
    else:
        logger.info("Generating random topic")
        topic_generator = TopicGenerator()
        topic = topic_generator.generate_topic()
        logger.info(f"Generated topic: {topic.title}")
    
    # Generate conversation
    logger.info("Generating conversation")
    conversation_generator = ConversationGenerator()
    conversation = conversation_generator.generate_conversation(topic, args.turns)
    
    # Log detailed info about conversation
    logger.info(f"Generated conversation with {len(conversation.turns)} turns (requested: {args.turns})")
    logger.info(f"Host: {conversation.host.name}, Guest: {conversation.guest.name}")
    
    # Print conversation sequence for debugging
    print("\nDEBUG - CONVERSATION SEQUENCE:")
    for i, turn in enumerate(conversation.turns):
        speaker_name = conversation.host.name if turn.speaker == Role.HOST else conversation.guest.name
        print(f"{i+1}. {speaker_name}: {turn.text[:50]}..." if len(turn.text) > 50 else f"{i+1}. {speaker_name}: {turn.text}")
    print()
    
    # Generate audio
    logger.info("Generating audio")
    episode_id = generate_episode_id()
    audio_processor = AudioProcessor(client)
    episode = audio_processor.generate_podcast_audio(conversation, episode_id)
    
    # Output results
    logger.info(f"Podcast episode generated: {episode.final_audio_path}")
    logger.info(f"Total duration: {episode.metadata.get('duration', 'unknown')} seconds")
    
    # Save transcript
    transcript_path = os.path.join(Config.TRANSCRIPT_DIR, f"{episode_id}_transcript.txt")
    with open(transcript_path, "w") as f:
        f.write(f"Title: {topic.title}\n")
        f.write(f"Host: {conversation.host.name}\n")
        f.write(f"Guest: {conversation.guest.name}\n\n")
        
        for turn in conversation.turns:
            speaker_name = conversation.host.name if turn.speaker == "host" else conversation.guest.name
            f.write(f"{speaker_name}: {turn.text}\n\n")
    
    logger.info(f"Transcript saved to: {transcript_path}")


if __name__ == "__main__":
    main() 
