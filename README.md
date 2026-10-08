# Audiobook Reader

Paste a long piece of text and have it read aloud like an audiobook with ElevenLabs voices.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your ElevenLabs API key in .env
python app.py
```

Open http://127.0.0.1:5000, paste text, pick a voice, and press **Start reading**.

## How it works

- The text is split into passages of about 1,500 characters, breaking on paragraphs and then sentences.
- Playback starts as soon as the first passage is generated. The next two are generated in the background, so there's no gap between passages.
- Each request sends the neighbouring text as `previous_text` / `next_text`, which keeps the narrator's intonation consistent across passage boundaries.
- Click any paragraph to jump to it. Space toggles play/pause, the arrow keys skip passages.
- **Download MP3** generates any remaining passages and saves the whole thing as one file.
- Generated audio is cached in memory on the server, so replaying a passage doesn't cost credits again (the cache resets when you restart the app).

## Credits

ElevenLabs bills per character. Multilingual v2 costs 1 credit per character; Flash v2.5 costs half that. Audio is only generated for passages you actually reach (plus two ahead), unless you press Download.
