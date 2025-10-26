# AI Movie Generator

A futuristic Flask-based application that generates cinematic movies using AI. The application uses Gemini AI for script generation, FLUX for image generation, and Wan for video generation.

## Features

- 🎬 Multi-step movie creation process
- 🎨 Futuristic UI/UX with animations
- 📝 AI-powered script generation using Gemini
- 🖼️ Scene-by-scene image generation
- 🎥 Video generation from images using Wan AI
- 🔊 Audio integration ready (ElevenLabs)
- 📱 Responsive design
- 🚀 ngrok tunnel for easy access

## Prerequisites

- Python 3.8 or higher
- CUDA-compatible GPU (recommended for video generation)
- API Keys:
  - Gemini API Key
  - ElevenLabs API Key (optional)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd movie
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

4. Create necessary directories:
```bash
mkdir -p static/uploads static/output
```

## Usage

1. Run the application:
```bash
python app.py
```

2. Access the application:
- Local: `http://localhost:5000`
- ngrok URL will be displayed in the console

3. Create your movie:
   - Enter movie details (title, genre, description, style)
   - Review and approve the generated script
   - Approve generated images for each scene
   - Generate the final video
   - Download or share your movie

## API Endpoints

- `GET /` - Landing page
- `GET /create` - Movie creation page
- `POST /generate_script` - Generate movie script
- `POST /generate_image` - Generate scene image
- `POST /generate_video` - Generate video from images
- `POST /generate_poster` - Generate movie poster
- `GET /download/<filename>` - Download generated files

## Technologies Used

- **Backend**: Flask
- **AI Models**:
  - Gemini (Script Generation)
  - FLUX (Image Generation)
  - Wan AI (Video Generation)
  - ElevenLabs (Audio - ready for integration)
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with futuristic themes
- **Tunneling**: ngrok

## Project Structure

```
movie/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html        # Landing page
│   └── create.html       # Movie creation page
├── static/
│   ├── css/
│   │   └── style.css     # Styles
│   ├── js/
│   │   ├── main.js       # Landing page JS
│   │   └── create.js     # Creation workflow JS
│   ├── uploads/          # User uploads
│   └── output/           # Generated content
└── README.md
```

## Notes

- Video generation requires significant GPU memory
- The application is optimized for CUDA-enabled systems
- For CPU-only systems, video generation will be slower
- Images are generated as placeholders - integrate FLUX API for production

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
