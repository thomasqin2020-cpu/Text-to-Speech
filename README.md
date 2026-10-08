# Audiobook Reader

Paste a long piece of text and have it read aloud like an audiobook with ElevenLabs voices.

## Deploy on Vercel

1. Import the repo at https://vercel.com/new. No framework preset is needed; Vercel picks up the functions in `api/` and the page in `public/`.
2. In the project's **Settings → Environment Variables**, add `ELEVENLABS_API_KEY` with your key from https://elevenlabs.io/app/settings/api-keys.
3. Redeploy (Deployments → ⋯ → Redeploy). Environment variables only apply to deployments made after they're added.

If the page loads but says the key is missing, step 2 or 3 was skipped.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your ElevenLabs API key in .env
python dev.py
```

Open http://127.0.0.1:5000, paste text, pick a voice, and press **Start reading**.

## Features

- Two engines: ElevenLabs (your account's voices, billed per character) or the browser's built-in speech (free, unlimited, lower quality).
- Voice previews, labels (gender, accent, age), and stability / similarity / style tuning.
- Word count, listening-time estimate, and credit estimate before you commit.
- Playback: speed 0.75× to 2×, 15-second skips, scrubbing, sleep timer, keyboard shortcuts.
- Resume where you left off; the text and position are remembered in the browser.
- Open or drag in a `.txt` file. Chapter headings are detected and styled.
- Download the whole thing as one MP3 (ElevenLabs engine only).
- Light and dark themes.

## How it works

- The text is split into passages of about 1,000 characters, breaking on paragraphs and then sentences.
- Playback starts as soon as the first passage is generated. The next two are generated in the background, so there's no gap between passages.
- Each request sends the neighbouring text as `previous_text` / `next_text`, which keeps the narrator's intonation consistent across passage boundaries.
- Click any paragraph to jump to it. Space toggles play/pause, the arrow keys skip passages.
- **Download MP3** generates any remaining passages and saves the whole thing as one file.
- Each passage is generated once per session and kept in the browser, so replaying or seeking back doesn't cost credits again.

## Credits

ElevenLabs bills per character. Multilingual v2 costs 1 credit per character; Flash v2.5 costs half that. Audio is only generated for passages you actually reach (plus two ahead), unless you press Download.
