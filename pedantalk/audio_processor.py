import os
import random
import subprocess
import glob
from pathlib import Path
from typing import Any, List, Optional, Tuple

import ffmpeg

from pedantalk.config import Config
from pedantalk.models import AudioSegment, Conversation, DialogueTurn, PodcastEpisode, Role, Speaker


class AudioProcessor:
    """Processor for generating and combining audio files for the podcast."""
    
    def __init__(self, openai_client: Any) -> None:
        """
        Initialize the audio processor.
        
        Args:
            openai_client: The OpenAI client object.
        """
        self.client = openai_client
        Config.ensure_directories()
        
        # Clean up audio directory at startup to avoid accumulation of temp files
        self._cleanup_audio_directory()
    
    def _cleanup_audio_directory(self) -> None:
        """
        Clean up the audio directory by removing all temporary audio files.
        This helps prevent accumulation of files from previous runs,
        especially when they ended abnormally.
        """
        print(f"Cleaning up audio directory: {Config.AUDIO_DIR}")
        audio_files = glob.glob(os.path.join(Config.AUDIO_DIR, "*.flac"))
        concat_files = glob.glob(os.path.join(Config.AUDIO_DIR, "concat*.txt"))
        
        # Count removed files for logging
        removed_count = 0
        
        # Remove audio files
        for file_path in audio_files + concat_files:
            try:
                os.remove(file_path)
                removed_count += 1
            except OSError as e:
                print(f"Error removing file {file_path}: {e}")
        
        print(f"Removed {removed_count} temporary files from audio directory")
    
    def _get_voice_for_role(self, role: Role) -> str:
        """
        Get the voice name for a specific role.
        
        Args:
            role: The speaker role.
            
        Returns:
            str: The voice name.
        """
        return Config.HOST_VOICE if role == Role.HOST else Config.GUEST_VOICE
    
    def _generate_audio_for_turn(self, turn: DialogueTurn, episode_id: str, conversation: Conversation) -> AudioSegment:
        """
        Generate audio for a single conversation turn.
        
        Args:
            turn: The dialogue turn.
            episode_id: Unique identifier for the episode.
            conversation: The full conversation context to get speaker details.
            
        Returns:
            AudioSegment: The generated audio segment.
        """
        voice = self._get_voice_for_role(turn.speaker)
        filename = f"{episode_id}_{turn.speaker.value}_{random.randint(1000, 9999)}.flac"
        output_path = os.path.join(Config.AUDIO_DIR, filename)
        
        # Get voice instruction if available
        voice_instruction = None
        if turn.speaker == Role.HOST and conversation.host.voice_instruction:
            voice_instruction = conversation.host.voice_instruction
        elif turn.speaker == Role.GUEST and conversation.guest.voice_instruction:
            voice_instruction = conversation.guest.voice_instruction
        
        # Create speech with OpenAI
        speech_params = {
            "model": "tts-1",
            "voice": voice,
            "input": turn.text,
            "response_format": "flac"
        }
        
        # Add voice instructions if available (note: it's "voice_instructions" with 's', not "voice_instruction")
        if voice_instruction:
            print(f"Note: Using voice '{voice}' with instruction: {voice_instruction}")
            speech_params["instructions"] = voice_instruction
        
        response = self.client.audio.speech.create(**speech_params)
        
        # Save the audio file
        response.stream_to_file(output_path)
        
        # Get duration using ffmpeg
        probe = ffmpeg.probe(output_path)
        
        # Extract duration more robustly - handle different ffmpeg probe structures
        duration_ms = 0
        if "format" in probe and "duration" in probe["format"]:
            # Standard location
            duration_ms = int(float(probe["format"]["duration"]) * 1000)
        elif "streams" in probe and len(probe["streams"]) > 0 and "duration" in probe["streams"][0]:
            # Sometimes duration is in the first stream for FLAC files
            duration_ms = int(float(probe["streams"][0]["duration"]) * 1000)
        else:
            # Fallback: Use a default duration if we can't determine it
            print(f"Warning: Could not determine duration for {output_path}. Using 3 seconds as default.")
            duration_ms = 3000
        
        return AudioSegment(
            speaker=turn.speaker,
            text=turn.text,
            audio_path=output_path,
            duration_ms=duration_ms
        )
    
    def _generate_silence(self, min_ms: int, max_ms: int, episode_id: str) -> str:
        """
        Generate a silent audio segment.
        
        Args:
            min_ms: Minimum silence duration in milliseconds.
            max_ms: Maximum silence duration in milliseconds.
            episode_id: Unique identifier for the episode.
            
        Returns:
            str: Path to the generated silence file.
        """
        duration_ms = random.randint(min_ms, max_ms)
        duration_s = duration_ms / 1000.0
        filename = f"{episode_id}_silence_{random.randint(1000, 9999)}.flac"
        output_path = os.path.join(Config.AUDIO_DIR, filename)
        
        # Create silence using ffmpeg
        ffmpeg.input(f"anullsrc=r=44100:cl=stereo", t=duration_s, f="lavfi").output(
            output_path, acodec="flac", ar="44100").overwrite_output().run(quiet=True)
        
        return output_path
    
    def _create_concat_file(self, audio_files: List[str], concat_file_path: str) -> None:
        """
        Create a concat file for ffmpeg.
        
        Args:
            audio_files: List of audio file paths.
            concat_file_path: Path to save the concat file.
        """
        with open(concat_file_path, 'w') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file}'\n")
    
    def _combine_audio_files(self, audio_files: List[str], output_path: str) -> None:
        """
        Combine multiple audio files using ffmpeg.
        
        Args:
            audio_files: List of audio file paths.
            output_path: Output file path.
        """
        # Verify all input files exist
        for audio_file in audio_files:
            if not os.path.exists(audio_file):
                print(f"Warning: Audio file does not exist: {audio_file}")
        
        # Only proceed with files that exist
        valid_audio_files = [f for f in audio_files if os.path.exists(f)]
        
        if not valid_audio_files:
            print("Error: No valid audio files to combine")
            return
            
        # Create concat file
        concat_file = os.path.join(Config.AUDIO_DIR, "concat.txt")
        self._create_concat_file(valid_audio_files, concat_file)
        
        # Debug: show content of concat file
        print(f"Debug: Contents of concat file ({concat_file}):")
        with open(concat_file, 'r') as f:
            print(f.read())
        
        # Try multiple methods to combine audio files
        success = False
        errors = []
        
        # Method 1: Standard ffmpeg-python concat
        try:
            print(f"Method 1: Running ffmpeg-python to combine {len(valid_audio_files)} audio files...")
            ffmpeg.input(concat_file, f="concat", safe=0).output(
                output_path, acodec="flac", ar="44100").overwrite_output().run()
            print(f"Success! Combined audio files to: {output_path}")
            success = True
        except ffmpeg._run.Error as e:
            errors.append(f"Method 1 failed: {e}")
            print(f"Method 1 failed: {e}")
        
        # Method 2: Direct subprocess call if method 1 failed
        if not success:
            try:
                print("Method 2: Trying direct subprocess call...")
                cmd = [
                    "ffmpeg", 
                    "-f", "concat", 
                    "-safe", "0", 
                    "-i", concat_file, 
                    "-c:a", "flac", 
                    "-ar", "44100", 
                    "-y", 
                    output_path
                ]
                process = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if process.returncode != 0:
                    errors.append(f"Method 2 failed: {process.stderr}")
                    print(f"Method 2 failed: {process.stderr}")
                else:
                    print("Method 2 succeeded!")
                    success = True
            except Exception as sub_e:
                errors.append(f"Method 2 exception: {sub_e}")
                print(f"Method 2 exception: {sub_e}")
        
        # Method 3: Use filtercomplex for concat if previous methods failed
        if not success:
            try:
                print("Method 3: Trying filter_complex approach...")
                # Create filter_complex input string
                inputs = []
                filter_parts = []
                
                for i, file in enumerate(valid_audio_files):
                    inputs.extend(["-i", file])
                    filter_parts.append(f"[{i}:0]")
                
                filter_complex = f"{' '.join(filter_parts)}concat=n={len(valid_audio_files)}:v=0:a=1[out]"
                
                cmd = [
                    "ffmpeg",
                    *inputs,
                    "-filter_complex", filter_complex,
                    "-map", "[out]",
                    "-y", output_path
                ]
                
                print(f"Running command: {' '.join(cmd)}")
                process = subprocess.run(cmd, capture_output=True, text=True, check=False)
                
                if process.returncode != 0:
                    errors.append(f"Method 3 failed: {process.stderr}")
                    print(f"Method 3 failed: {process.stderr}")
                else:
                    print("Method 3 succeeded!")
                    success = True
            except Exception as e:
                errors.append(f"Method 3 exception: {e}")
                print(f"Method 3 exception: {e}")
        
        # Clean up
        if os.path.exists(concat_file):
            os.remove(concat_file)
            
        # Raise exception if all methods failed
        if not success:
            raise RuntimeError(f"Failed to combine audio files. Errors: {errors}")
    
    def generate_podcast_audio(self, conversation: Conversation, episode_id: str) -> PodcastEpisode:
        """
        Generate audio for an entire podcast episode.
        
        Args:
            conversation: The podcast conversation.
            episode_id: Unique identifier for the episode.
            
        Returns:
            PodcastEpisode: The complete podcast episode with audio.
        """
        # Create episode
        episode = PodcastEpisode(
            topic=conversation.topic,
            host=conversation.host,
            guest=conversation.guest,
            conversation=conversation.turns
        )
        
        # Generate audio for each turn
        audio_segments: List[AudioSegment] = []
        all_audio_files: List[str] = []
        
        for turn in conversation.turns:
            # Add a silence before each turn (except the first)
            if all_audio_files:
                silence_file = self._generate_silence(
                    Config.SILENCE_MIN_MS, 
                    Config.SILENCE_MAX_MS, 
                    episode_id
                )
                all_audio_files.append(silence_file)
            
            # Generate audio for the turn
            audio_segment = self._generate_audio_for_turn(turn, episode_id, conversation)
            audio_segments.append(audio_segment)
            all_audio_files.append(audio_segment.audio_path)
        
        # Combine all audio files
        final_output_path = os.path.join(Config.OUTPUT_DIR, f"{episode_id}_final.flac")
        self._combine_audio_files(all_audio_files, final_output_path)
        
        # Update and return the episode
        episode.audio_segments = audio_segments
        episode.final_audio_path = final_output_path
        episode.metadata = {
            "episode_id": episode_id,
            "topic": conversation.topic.title,
            "host": conversation.host.name,
            "guest": conversation.guest.name,
            "duration": str(sum(segment.duration_ms for segment in audio_segments) / 1000.0)
        }
        
        return episode 
