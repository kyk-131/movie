# Quick Start Guide

Get your AI Movie Generator up and running in minutes!

## Prerequisites

- Python 3.8 or higher
- CUDA-compatible GPU (optional but recommended)
- API Keys:
  - Gemini API Key: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Optional: ElevenLabs API Key for voice generation

## Installation

### 1. Clone and Navigate

```bash
cd f:\movie
```

### 2. Install Dependencies

Option A - Automatic:
```bash
python setup.py
```

Option B - Manual:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here  # Optional
NGROK_AUTHTOKEN=your_ngrok_token_here  # Optional
```

### 4. Run the Application

```bash
python app.py
```

### 5. Access the Application

- **Local**: http://localhost:5000
- **Ngrok URL**: Will be displayed in console (if configured)

## Usage Flow

1. **Landing Page**: Click "Create Movie"
2. **Enter Details**: Fill in title, genre, description, and style
3. **Generate Script**: AI generates a multi-scene script
4. **Review & Approve**: Review the script, regenerate if needed
5. **Generate Images**: AI creates images for each scene
6. **Approve Images**: Regenerate or approve each scene image
7. **Create Video**: AI converts images to video
8. **Final Result**: View, download, or share your movie

## Troubleshooting

### "Gemini API not configured"
- Make sure your `.env` file contains `GEMINI_API_KEY`

### Video generation fails
- Check if you have a GPU installed
- Reduce video resolution in `app.py` if memory issues occur

### ngrok not working
- Install ngrok: `pip install pyngrok`
- Or set `NGROK_AUTHTOKEN` in `.env`

## Tips

- Start with simple descriptions for faster results
- GPU acceleration significantly speeds up video generation
- Generated files are saved in `static/output/`
- Each generation uses API credits (be mindful of costs)

## Support

Check the full `README.md` for detailed documentation.
