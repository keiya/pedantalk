# pedantalk

**pedantalk** is an automated AI-generated podcast where two LLM-powered participants—a curious host with limited specialized knowledge and a topic-specific expert guest—engage in thoughtful dialogues.

## Project Overview

- Automated, AI-driven podcast episodes.
- Dynamic conversation between two AI personalities (host & expert guest).
- Conversations generated via OpenAI's language models.
- Audio synthesis through OpenAI's TTS (text-to-speech).
- Concatenation and audio processing via FFmpeg.

## Key Features

### Automated Topic Generation

- Each episode features a randomly-generated high-level topic (e.g., AI, consciousness, philosophy, technology).
- Topics are generated automatically using LLM prompts.

### AI Personalities

#### Host

- Personality: Curious, intellectually engaged.
- Intelligence: Approximately IQ 120.
- Knowledge Level: Equivalent to a liberal arts college sophomore.
- Limitations: Limited specialized expertise, facilitating simplified, accessible conversation.

#### Expert Guest

- Personality and expertise dynamically tailored to the generated episode topic.
- Deep knowledge in specialized fields relevant to the topic.

### Conversation Flow

- The host initiates the conversation with the provided topic.
- Host and guest alternate turns in conversation, scripted separately for distinct speech synthesis.
- Dialogue generation respects role-based constraints (host’s limited knowledge vs. guest’s expertise).

## Audio Generation Pipeline

1. **Script Generation**: Scripts separately generated for host and guest.
2. **Speech Synthesis**: Convert scripts into audio files via OpenAI TTS.
3. **Audio Processing**:
   - Combine separate audio files using FFmpeg.
   - Random-length silence intervals inserted between speech segments for natural pacing.

## Technologies Used

- **OpenAI GPT Models**: Dialogue and content generation.
- **OpenAI TTS API**: Text-to-speech audio synthesis.
- **FFmpeg**: Audio processing and concatenation.

## Language

- All dialogues, audio synthesis, and outputs are in English.

## Setup and Usage

To get started:

- Create and activate a virtual environment: `make setup && source venv/bin/activate`

- Install dependencies: `make install`
- Run type checking: `make type-check`
- Run linting: `make lint`
- Format code: `make format`
- Run the application: `make run`

---

Enjoy exploring intellectual curiosity with **pedantalk**—making complex topics accessible through engaging AI conversations!
