# VoiceShield AI

VoiceShield is a small web app for screening short voice recordings for signs
associated with AI-generated speech. It uses a fine-tuned audio-classification
checkpoint; the original `facebook/wav2vec2-base` checkpoint did not contain a
trained real/fake classification head.

## Run locally

Use Python 3.12 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend-requirements.txt
python main.py
```

Open [http://localhost:7860](http://localhost:7860). The first analysis
downloads the model from Hugging Face and can take a few minutes.

## Audio limits

- WAV or FLAC uploads; microphone recordings are converted to WAV in the browser
- At most 4 MB and 60 seconds; at least 1 second
- Audio is decoded and analyzed in memory, not saved to disk

## Deployment

The Render blueprint uses the free web-service plan and serves the application
without requiring a payment method. Free instances have limited memory and spin
down when idle. Audio analysis is explicitly disabled in this free deployment
because the model requires at least 1 GiB of memory; the public site reports
this instead of claiming to analyze audio.

The Vercel project can serve the same `index.html` and forward `/api/analyze` to
Render. Deploy Render first, then set the Vercel `RENDER_API_URL` environment
variable to the Render service URL (for example,
`https://voiceshield-api.onrender.com`). The Vercel function uses a 60-second
maximum duration; a plan that supports that duration is required.

## Limitations

This is an estimate, not proof that a voice is real or synthetic. Model
performance varies across recording conditions, languages, accents, codecs,
and synthesis tools. Do not rely on this result alone for high-stakes
decisions.