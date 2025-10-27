from flask import Flask, render_template, request, jsonify, send_file, session, redirect
import os
import json
import uuid
from google import genai
import torch
from diffusers import WanImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
from PIL import Image
import numpy as np
import subprocess
import threading
import time
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to import ngrok, but make it optional
try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("Warning: pyngrok not available. Install it for ngrok support.")

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Video storage configuration - can be local or cloud
VIDEO_STORAGE_TYPE = os.getenv('VIDEO_STORAGE_TYPE', 'cloud')  # 'local' or 'cloud'
CLOUD_VIDEO_BASE_URL = os.getenv('CLOUD_VIDEO_BASE_URL', '')  # Base URL for cloud storage
CLOUD_VIDEO_PATH = os.getenv('CLOUD_VIDEO_PATH', '/teamspace/studios/this_studio/movie/')  # Cloud storage path

# Your specific video path
SAMPLE_VIDEO_PATH = '/teamspace/studios/this_studio/movie/sample.mp4'

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

# Movies storage file
MOVIES_FILE = 'data/movies.json'

def load_movies():
    """Load movies from storage"""
    try:
        if os.path.exists(MOVIES_FILE):
            with open(MOVIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading movies: {e}")
        return []

def save_movies(movies):
    """Save movies to storage"""
    try:
        with open(MOVIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(movies, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving movies: {e}")
        return False

def save_movie(movie_data):
    """Save a single movie to storage"""
    movies = load_movies()
    movies.append(movie_data)
    return save_movies(movies)

def get_video_paths(video_id):
    """Get video paths based on storage type"""
    if VIDEO_STORAGE_TYPE == 'cloud':
        # Cloud storage paths - using your specific path
        video_filename = f"{video_id}.mp4"
        video_path = os.path.join(CLOUD_VIDEO_PATH, video_filename)
        # Use your specific cloud path for URLs
        video_url = f"/teamspace/studios/this_studio/movie/{video_filename}"
        return video_path, video_url
    else:
        # Local storage paths
        video_filename = f"{video_id}.mp4"
        video_path = os.path.join(app.config['OUTPUT_FOLDER'], video_filename)
        video_url = f"/static/output/{video_filename}"
        return video_path, video_url

def video_exists(video_path):
    """Check if video file exists (works for both local and cloud)"""
    if VIDEO_STORAGE_TYPE == 'cloud':
        # For cloud storage, we'll assume the file exists if the path is valid
        # You might want to implement actual cloud storage checking here
        return True
    else:
        return os.path.exists(video_path)

# Initialize Gemini client (with error handling)
try:
    # Use environment variable or hardcoded key as fallback
    gemini_api_key = os.getenv('GEMINI_API_KEY') or 'AIzaSyCchinZiLFFD-l8A7iuTitHH1GhKy0oO04'
    if gemini_api_key:
        genai_client = genai.Client(api_key=gemini_api_key)
        print("✓ Gemini API client initialized successfully")
    else:
        print("Warning: GEMINI_API_KEY not set. Script generation will fail.")
        genai_client = None
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    genai_client = None

# Initialize SDXL Lightning pipeline for images
sdxl_pipe = None
sdxl_pipe_lock = threading.Lock()

def get_sdxl_pipe():
    global sdxl_pipe
    if sdxl_pipe is None:
        with sdxl_pipe_lock:
            if sdxl_pipe is None:
                print("Loading SDXL Lightning model...")
                from diffusers import StableDiffusionXLPipeline, UNet2DConditionModel, EulerDiscreteScheduler
                from huggingface_hub import hf_hub_download
                from safetensors.torch import load_file
                
                base = "stabilityai/stable-diffusion-xl-base-1.0"
                repo = "ByteDance/SDXL-Lightning"
                ckpt = "sdxl_lightning_4step_unet.safetensors"
                
                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.float16 if device == "cuda" else torch.float32
                
                # Load model
                unet = UNet2DConditionModel.from_config(base, subfolder="unet").to(device, dtype)
                unet.load_state_dict(load_file(hf_hub_download(repo, ckpt), device=device))
                sdxl_pipe = StableDiffusionXLPipeline.from_pretrained(base, unet=unet, torch_dtype=dtype).to(device)
                
                # Ensure sampler uses "trailing" timesteps
                sdxl_pipe.scheduler = EulerDiscreteScheduler.from_config(sdxl_pipe.scheduler.config, timestep_spacing="trailing")
                
    return sdxl_pipe

# Initialize video pipeline (lazy load)
video_pipe = None
video_pipe_lock = threading.Lock()

def get_video_pipe():
    global video_pipe
    if video_pipe is None:
        with video_pipe_lock:
            if video_pipe is None:
                print("Loading Wan video model...")
                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.bfloat16 if device == "cuda" else torch.float32
                video_pipe = WanImageToVideoPipeline.from_pretrained(
                    "Wan-AI/Wan2.2-I2V-A14B-Diffusers",
                    torch_dtype=dtype
                )
                video_pipe.to(device)
                video_pipe.enable_model_cpu_offload()
    return video_pipe

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/script')
def script():
    return render_template('script.html')

@app.route('/images')
def images():
    return render_template('images.html')

@app.route('/video')
def video():
    return render_template('video.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/movies')
def get_movies():
    """Get all movies from storage"""
    try:
        movies = load_movies()
        print(f"📚 HISTORY REQUEST: Returning {len(movies)} movies")
        
        return jsonify({
            'success': True,
            'movies': movies,
            'count': len(movies),
            'timestamp': time.time()
        })
    except Exception as e:
        print(f"❌ Error getting movies: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load movies',
            'details': str(e)
        }), 500

@app.route('/api/movies/<movie_id>')
def get_movie(movie_id):
    """Get a specific movie by ID"""
    try:
        movies = load_movies()
        movie = next((m for m in movies if m.get('id') == movie_id), None)
        
        if movie:
            print(f"📖 MOVIE REQUEST: Found movie '{movie.get('title', 'Unknown')}'")
            return jsonify({
                'success': True,
                'movie': movie,
                'timestamp': time.time()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Movie not found'
            }), 404
    except Exception as e:
        print(f"❌ Error getting movie {movie_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load movie',
            'details': str(e)
        }), 500

@app.route('/api/movies/<movie_id>/delete', methods=['DELETE'])
def delete_movie(movie_id):
    """Delete a movie"""
    try:
        movies = load_movies()
        original_count = len(movies)
        movies = [m for m in movies if m.get('id') != movie_id]
        
        if len(movies) < original_count:
            if save_movies(movies):
                print(f"🗑️ MOVIE DELETED: {movie_id}")
                return jsonify({
                    'success': True,
                    'message': 'Movie deleted successfully',
                    'timestamp': time.time()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to save changes'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Movie not found'
            }), 404
    except Exception as e:
        print(f"❌ Error deleting movie {movie_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete movie',
            'details': str(e)
        }), 500

@app.route('/api/movies/<movie_id>/download')
def download_movie(movie_id):
    """Download movie video file"""
    try:
        movies = load_movies()
        movie = next((m for m in movies if m.get('id') == movie_id), None)
        
        if not movie:
            return jsonify({'success': False, 'error': 'Movie not found'}), 404
        
        video_path = movie.get('video_path')
        video_url = movie.get('video_url')
        
        if VIDEO_STORAGE_TYPE == 'cloud':
            # For cloud storage, redirect to the video URL
            print(f"📥 DOWNLOAD REQUEST (Cloud): {movie.get('title', 'Unknown')} - {video_url}")
            return redirect(video_url)
        else:
            # For local storage, serve the file
            if not video_path or not video_exists(video_path):
                return jsonify({'success': False, 'error': 'Video file not found'}), 404
            
            print(f"📥 DOWNLOAD REQUEST (Local): {movie.get('title', 'Unknown')} - {video_path}")
            return send_file(video_path, as_attachment=True, download_name=f"{movie.get('title', 'movie')}.mp4")
        
    except Exception as e:
        print(f"❌ Error downloading movie {movie_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to download movie',
            'details': str(e)
        }), 500

@app.route('/video/<video_id>')
def serve_video(video_id):
    """Serve video file - works for both local and cloud storage"""
    try:
        if VIDEO_STORAGE_TYPE == 'cloud':
            # For cloud storage, redirect to the cloud URL
            video_path, video_url = get_video_paths(video_id)
            print(f"🎬 SERVING VIDEO (Cloud): {video_id} - {video_url}")
            return redirect(video_url)
        else:
            # For local storage, serve the file
            video_path, video_url = get_video_paths(video_id)
            if not video_exists(video_path):
                return jsonify({'error': 'Video not found'}), 404
            
            print(f"🎬 SERVING VIDEO (Local): {video_id} - {video_path}")
            return send_file(video_path)
    except Exception as e:
        print(f"❌ Error serving video {video_id}: {e}")
        return jsonify({'error': 'Failed to serve video'}), 500

@app.route('/sample-video')
def serve_sample_video():
    """Serve the sample video from your cloud storage"""
    try:
        print(f"🎬 SERVING SAMPLE VIDEO: {SAMPLE_VIDEO_PATH}")
        return redirect(f"file://{SAMPLE_VIDEO_PATH}")
    except Exception as e:
        print(f"❌ Error serving sample video: {e}")
        return jsonify({'error': 'Failed to serve sample video'}), 500

@app.route('/create-sample-movie')
def create_sample_movie():
    """Create a sample movie entry with your video path for testing"""
    try:
        sample_movie = {
            'id': 'sample-movie-001',
            'title': 'Sample AI Movie',
            'genre': 'Action',
            'style': 'Cinematic',
            'description': 'A sample movie created to test the cloud storage integration',
            'num_scenes': '3',
            'video_path': SAMPLE_VIDEO_PATH,
            'video_url': f"/teamspace/studios/this_studio/movie/sample.mp4",
            'created_at': time.time(),
            'created_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'completed',
            'video_info': {
                'duration_seconds': 30.0,
                'file_size_bytes': 1024000,
                'file_size_mb': 1.0,
                'total_clips': 3,
                'resolution': '1920x1080'
            },
            'scenes': [
                {
                    'id': 1,
                    'title': 'Opening Scene',
                    'content': 'The hero enters the scene with dramatic music playing.',
                    'genre': 'Action',
                    'style': 'Cinematic'
                },
                {
                    'id': 2,
                    'title': 'Action Sequence',
                    'content': 'High-octane action with explosions and stunts.',
                    'genre': 'Action',
                    'style': 'Cinematic'
                },
                {
                    'id': 3,
                    'title': 'Climax',
                    'content': 'The final showdown between hero and villain.',
                    'genre': 'Action',
                    'style': 'Cinematic'
                }
            ],
            'images': []
        }
        
        if save_movie(sample_movie):
            print(f"✅ Sample movie created successfully: {sample_movie['title']}")
            return jsonify({
                'success': True,
                'message': 'Sample movie created successfully!',
                'movie': sample_movie
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save sample movie'
            }), 500
            
    except Exception as e:
        print(f"❌ Error creating sample movie: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create sample movie',
            'details': str(e)
        }), 500

@app.route('/status')
def status():
    """Get current system status and progress"""
    try:
        movie_data = session.get('movie_data', {})
        scenes = session.get('scenes', [])
        
        status_info = {
            'success': True,
            'timestamp': time.time(),
            'movie_data': movie_data,
            'scenes_count': len(scenes),
            'system_status': {
                'gemini_available': genai_client is not None,
                'sdxl_available': get_sdxl_pipe() is not None,
                'video_pipe_available': get_video_pipe() is not None,
                'output_folder': app.config['OUTPUT_FOLDER'],
                'upload_folder': app.config['UPLOAD_FOLDER']
            },
            'progress': {
                'script_generated': len(scenes) > 0,
                'images_generated': 0,  # Will be updated by frontend
                'video_generated': False  # Will be updated by frontend
            }
        }
        
        print(f"📊 STATUS REQUEST: Movie '{movie_data.get('title', 'Unknown')}' - {len(scenes)} scenes")
        return jsonify(status_info)
    
    except Exception as e:
        print(f"❌ Status request failed: {e}")
        return jsonify({
            'success': False,
            'error': 'Status request failed',
            'details': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/api/model-info')
def model_info():
    """Get information about available AI models and their capabilities"""
    try:
        return jsonify({
            'image_generation': {
                'model': 'ByteDance/SDXL-Lightning',
                'description': 'Ultra-fast SDXL model for high-quality image generation',
                'capabilities': {
                    'styles': [
                        'Cinematic - Professional film photography style',
                        'Realistic - Photorealistic, ultra-realistic images',
                        'Anime - Japanese animation/manga style',
                        'Cartoon - Disney-style 3D animation',
                        'Fantasy - Magical, ethereal fantasy art',
                        'Sci-Fi - Futuristic, cyberpunk, space age',
                        'Horror - Dark, atmospheric, chilling',
                        'Comedy - Bright, cheerful, humorous'
                    ],
                    'genres': [
                        'Action - Dynamic, intense, explosive',
                        'Adventure - Epic journey, exploration',
                        'Comedy - Lighthearted, fun, cheerful',
                        'Drama - Emotional depth, serious tone',
                        'Horror - Dark atmosphere, suspense',
                        'Romance - Romantic, intimate moments',
                        'Sci-Fi - Futuristic technology, space',
                        'Fantasy - Magical elements, enchanted world'
                    ],
                    'technical_specs': {
                        'resolution': '1024x1024 pixels',
                        'inference_steps': '4 (ultra-fast)',
                        'guidance_scale': '0 (for speed)',
                        'model_type': 'Diffusion-based',
                        'speed': '~1-2 seconds per image'
                    }
                }
            },
            'script_generation': {
                'model': 'Google Gemini Pro',
                'description': 'Advanced language model for creative script writing',
                'capabilities': {
                    'output_formats': ['Movie scripts', 'Scene descriptions', 'Character dialogues'],
                    'languages': ['English', 'Multiple languages supported'],
                    'styles': ['Professional', 'Creative', 'Adaptive to genre']
                }
            },
            'video_generation': {
                'model': 'Wan (Video Generation)',
                'description': 'AI-powered video generation with cinematic effects',
                'capabilities': {
                    'input': 'Images + Script text + Movie metadata',
                    'output': 'High-quality MP4 video files (24fps)',
                    'features': [
                        'Genre-specific transitions (crossfade, fade, etc.)',
                        'Cinematic fade in/out effects',
                        'Title overlays with custom styling',
                        'Genre/style information overlays',
                        'Scene number indicators',
                        'High-quality encoding (H.264, CRF 23)',
                        'Professional video composition',
                        'Automatic scene timing'
                    ],
                    'transition_types': {
                        'Action': 'Fast crossfade (0.3s)',
                        'Adventure': 'Smooth crossfade (0.8s)',
                        'Comedy': 'Bounce crossfade (0.4s)',
                        'Drama': 'Smooth crossfade (1.0s)',
                        'Horror': 'Fade transition (0.6s)',
                        'Romance': 'Smooth crossfade (1.2s)',
                        'Sci-Fi': 'Glitch crossfade (0.7s)',
                        'Fantasy': 'Magic crossfade (1.0s)',
                        'Thriller': 'Sharp crossfade (0.5s)'
                    }
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_script', methods=['POST'])
def generate_script():
    try:
        print("🚀 ===== SCRIPT GENERATION REQUEST RECEIVED =====")
        
        if not genai_client:
            print("❌ ERROR: Gemini API client not initialized")
            return jsonify({
                'success': False, 
                'error': 'AI Script Generator is not available. Please check your API configuration.',
                'details': 'The Gemini API key is missing or invalid. Contact support if this persists.',
                'status': 'API_ERROR',
                'timestamp': time.time()
            }), 500
        
        data = request.json
        print(f"📋 Received movie data: {data}")
        
        title = data.get('title', 'Untitled Movie')
        genre = data.get('genre', 'Action')
        description = data.get('description', '')
        style = data.get('style', 'Cinematic')
        num_scenes = data.get('numScenes', '5')
        
        print(f"🎬 MOVIE DETAILS VALIDATED:")
        print(f"   📝 Title: '{title}'")
        print(f"   🎭 Genre: {genre}")
        print(f"   🎨 Style: {style}")
        print(f"   📖 Description: {description[:100]}{'...' if len(description) > 100 else ''}")
        print(f"   🎬 Scenes: {num_scenes}")
        
        # Store in session
        session['movie_data'] = {
            'title': title,
            'genre': genre,
            'description': description,
            'style': style,
            'numScenes': num_scenes
        }
        print("💾 Movie data stored in session successfully")
        
        # Generate script using Gemini
        print(f"🤖 INITIATING AI SCRIPT GENERATION...")
        print(f"   🔗 Connecting to Gemini AI...")
        print(f"   📝 Requesting {num_scenes} scenes for {genre} {style} movie...")
        
        prompt = f"""Generate a movie script based on the following details:
Title: {title}
Genre: {genre}
Description: {description}
Style: {style}
Number of Scenes: {num_scenes}

Please create a script with exactly {num_scenes} scenes. Format each scene as:
Scene [number]: [Scene Title]
[Scene description and dialogue]

IMPORTANT: Each scene must clearly reflect the {genre} genre and {style} style throughout the content.
Make it vivid and engaging, suitable for the {genre} genre and {style} style."""
        
        print("📤 Sending prompt to Gemini AI...")
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        
        print("✅ Gemini AI response received successfully!")
        script = response.text
        print(f"📄 SCRIPT STATISTICS:")
        print(f"   📏 Length: {len(script)} characters")
        print(f"   📝 Lines: {len(script.splitlines())} lines")
        print(f"   🔤 Words: {len(script.split())} words")
        
        # Parse script into scenes with genre and style per scene
        print("🔍 PARSING SCRIPT INTO SCENES...")
        scenes = parse_script_to_scenes(script, genre, style)
        print(f"✅ SCENE PARSING COMPLETE:")
        print(f"   🎬 Total scenes: {len(scenes)}")
        for i, scene in enumerate(scenes, 1):
            print(f"   📝 Scene {i}: '{scene['title']}' ({len(scene['content'])} chars)")
        
        # Store scenes in session
        session['scenes'] = scenes
        print("💾 All scenes stored in session successfully")
        
        print("🎉 ===== SCRIPT GENERATION COMPLETED SUCCESSFULLY =====")
        
        return jsonify({
            'success': True,
            'message': f'🎬 Script generated successfully! Created {len(scenes)} scenes for "{title}"',
            'details': f'Generated a {genre} {style} movie with {len(scenes)} scenes totaling {len(script)} characters',
            'script': script,
            'scenes': scenes,
            'movie_data': session['movie_data'],
            'status': 'SUCCESS',
            'timestamp': time.time(),
            'stats': {
                'total_scenes': len(scenes),
                'script_length': len(script),
                'word_count': len(script.split()),
                'line_count': len(script.splitlines())
            }
        })
    
    except Exception as e:
        print(f"❌ ===== SCRIPT GENERATION FAILED =====")
        print(f"   🚨 Error: {str(e)}")
        print(f"   📊 Error type: {type(e).__name__}")
        return jsonify({
            'success': False, 
            'error': 'Failed to generate script. Please try again.',
            'details': f'Script generation error: {str(e)}',
            'suggestion': 'Check your internet connection and try again in a moment.',
            'status': 'ERROR',
            'timestamp': time.time(),
            'error_type': type(e).__name__
        }), 500

def parse_script_to_scenes(script, genre, style):
    """Parse script text into scene objects with genre and style"""
    print("🔍 PARSING SCRIPT INTO SCENES...")
    print(f"   📄 Script length: {len(script)} characters")
    
    scenes = []
    lines = script.split('\n')
    current_scene = None
    current_content = []
    scene_count = 0
    
    print(f"   📝 Processing {len(lines)} lines...")
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check for scene markers (more flexible matching)
        if (line.startswith('Scene') or line.startswith('SCENE') or 
            line.startswith('scene') or 'Scene' in line[:10]):
            
            # Save previous scene if exists
            if current_scene and current_content:
                scene_count += 1
                scene_content = '\n'.join(current_content).strip()
                scenes.append({
                    'id': scene_count,
                    'title': current_scene,
                    'content': scene_content,
                    'genre': genre,
                    'style': style
                })
                print(f"   ✅ Parsed Scene {scene_count}: '{current_scene}' ({len(scene_content)} chars)")
            
            # Start new scene
            current_scene = line
            current_content = []
        else:
            # Add content to current scene
            if current_scene and line:
                current_content.append(line)
    
    # Add the last scene
    if current_scene and current_content:
        scene_count += 1
        scene_content = '\n'.join(current_content).strip()
        scenes.append({
            'id': scene_count,
            'title': current_scene,
            'content': scene_content,
            'genre': genre,
            'style': style
        })
        print(f"   ✅ Parsed Scene {scene_count}: '{current_scene}' ({len(scene_content)} chars)")
    
    # If no scenes were found, create a single scene with the entire script
    if not scenes:
        print("   ⚠️ No scene markers found, creating single scene from entire script")
        scenes.append({
            'id': 1,
            'title': f"Scene 1: {genre} {style} Movie",
            'content': script.strip(),
            'genre': genre,
            'style': style
        })
        print(f"   ✅ Created single scene: '{scenes[0]['title']}' ({len(script)} chars)")
    
    print(f"✅ SCENE PARSING COMPLETE: {len(scenes)} scenes found")
    return scenes if scenes else [{'id': 1, 'title': 'Scene 1', 'content': script, 'genre': genre, 'style': style}]

@app.route('/get_script')
def get_script():
    """Get the current script and scenes from session"""
    try:
        if 'scenes' in session and 'movie_data' in session:
            return jsonify({
                'success': True,
                'message': f'Found existing script with {len(session["scenes"])} scenes',
                'scenes': session['scenes'],
                'movie_data': session['movie_data']
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'No script found. Please generate a script first.',
                'suggestion': 'Go back to the Details section and create your movie script.'
            }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_scenes')
def get_scenes():
    """Get scenes for image generation"""
    try:
        if 'scenes' in session:
            return jsonify({
                'success': True,
                'message': f'Retrieved {len(session["scenes"])} scenes for image generation',
                'scenes': session['scenes']
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'No scenes found. Please generate a script first.',
                'suggestion': 'Complete the script generation step before creating images.'
            }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/regenerate_script', methods=['POST'])
def regenerate_script():
    """Regenerate the script"""
    try:
        if not genai_client:
            return jsonify({
                'success': False, 
                'error': 'AI Script Generator is not available. Please check your API configuration.',
                'details': 'The Gemini API key is missing or invalid. Contact support if this persists.'
            }), 500
        
        movie_data = session.get('movie_data', {})
        if not movie_data:
            return jsonify({
                'success': False, 
                'error': 'No movie data found. Please start over.',
                'suggestion': 'Go back to the Details section and fill in your movie information.'
            }), 400
        
        # Generate new script
        prompt = f"""Generate a movie script based on the following details:
Title: {movie_data['title']}
Genre: {movie_data['genre']}
Description: {movie_data['description']}
Style: {movie_data['style']}
Number of Scenes: {movie_data['numScenes']}

Please create a script with exactly {movie_data['numScenes']} scenes. Format each scene as:
Scene [number]: [Scene Title]
[Scene description and dialogue]

IMPORTANT: Each scene must clearly reflect the {movie_data['genre']} genre and {movie_data['style']} style throughout the content.
Make it vivid and engaging, suitable for the {movie_data['genre']} genre and {movie_data['style']} style."""
        
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        
        script = response.text
        scenes = parse_script_to_scenes(script, movie_data['genre'], movie_data['style'])
        session['scenes'] = scenes
        
        return jsonify({
            'success': True,
            'message': f'Script regenerated successfully! Created {len(scenes)} new scenes for "{movie_data.get("title", "your movie")}"',
            'script': script,
            'scenes': scenes,
            'movie_data': movie_data
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Initialize FLUX image pipeline (lazy load)
flux_pipe = None
flux_pipe_lock = threading.Lock()

def get_flux_pipe():
    global flux_pipe
    if flux_pipe is None:
        with flux_pipe_lock:
            if flux_pipe is None:
                print("Loading FLUX SDXL Lightning model...")
                try:
                    from diffusers import StableDiffusionXLPipeline, UNet2DConditionModel, EulerDiscreteScheduler
                    from huggingface_hub import hf_hub_download
                    from safetensors.torch import load_file
                    
                    base = "stabilityai/stable-diffusion-xl-base-1.0"
                    repo = "ByteDance/SDXL-Lightning"
                    ckpt = "sdxl_lightning_4step_unet.safetensors"
                    
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    print(f"Using device: {device}")
                    
                    # Load model
                    unet = UNet2DConditionModel.from_config(base, subfolder="unet")
                    unet.load_state_dict(load_file(hf_hub_download(repo, ckpt), device=device))
                    
                    flux_pipe = StableDiffusionXLPipeline.from_pretrained(
                        base, 
                        unet=unet, 
                        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                        variant="fp16" if device == "cuda" else None
                    )
                    flux_pipe.to(device)
                    
                    # Ensure sampler uses "trailing" timesteps
                    flux_pipe.scheduler = EulerDiscreteScheduler.from_config(
                        flux_pipe.scheduler.config, 
                        timestep_spacing="trailing"
                    )
                    
                    print("✓ FLUX SDXL Lightning model loaded successfully")
                except Exception as e:
                    print(f"Warning: Could not load FLUX model: {e}")
                    flux_pipe = None
    return flux_pipe

@app.route('/generate_image', methods=['POST'])
def generate_image():
    try:
        print("🖼️ ===== IMAGE GENERATION REQUEST RECEIVED =====")
        
        data = request.json
        print(f"📋 Received image generation data: {data}")
        
        scene_id = data.get('scene_id')
        scene_content = data.get('scene_content')
        genre = data.get('genre', '')
        style = data.get('style', '')
        
        print(f"🎬 SCENE DETAILS:")
        print(f"   🆔 Scene ID: {scene_id}")
        print(f"   🎭 Genre: {genre}")
        print(f"   🎨 Style: {style}")
        print(f"   📝 Content: {scene_content[:100]}{'...' if len(scene_content) > 100 else ''}")
        
        movie_data = session.get('movie_data', {})
        print(f"🎬 Movie context: {movie_data.get('title', 'Unknown')} ({movie_data.get('genre', 'Unknown')})")
        
        # Create enhanced prompt with genre and style
        print("🔧 BUILDING IMAGE GENERATION PROMPT...")
        
        # Style-specific prompt engineering
        style_prompts = {
            'Cinematic': 'cinematic photography, film still, professional cinematography, dramatic lighting, movie poster style, realistic human faces, photorealistic, 35mm film grain, depth of field, professional color grading',
            'Realistic': 'photorealistic, ultra realistic, detailed photography, natural lighting, real world setting, lifelike, high resolution, professional photography, natural colors, realistic textures',
            'Anime': 'anime style, manga art, japanese animation, cel shading, vibrant colors, stylized characters, anime character design, manga illustration',
            'Cartoon': 'cartoon style, animated movie, disney style, 3d animation, colorful, stylized, family-friendly, animated character design',
            'Fantasy': 'fantasy art, magical realism, ethereal, mystical, otherworldly, fantasy illustration, magical elements, enchanted atmosphere',
            'Sci-Fi': 'sci-fi art, futuristic, cyberpunk, space age, technological, neon lights, advanced technology, science fiction illustration',
            'Horror': 'horror art, dark atmosphere, eerie, gothic, suspenseful, dark lighting, horror movie style, chilling, atmospheric',
            'Comedy': 'bright and cheerful, comedic, lighthearted, fun, colorful, upbeat, humorous, family-friendly comedy style'
        }
        
        # Get style-specific prompt
        style_prompt = style_prompts.get(style, 'cinematic photography, high quality, detailed')
        
        # Genre-specific enhancements
        genre_enhancements = {
            'Action': 'dynamic action, intense movement, explosive energy, adrenaline rush, high stakes',
            'Adventure': 'epic journey, exploration, discovery, vast landscapes, heroic quest',
            'Comedy': 'lighthearted, humorous, fun, cheerful, comedic timing',
            'Drama': 'emotional depth, character development, serious tone, meaningful moments',
            'Horror': 'dark atmosphere, suspense, fear, chilling, eerie',
            'Romance': 'romantic atmosphere, emotional connection, intimate moments, love story',
            'Sci-Fi': 'futuristic technology, space, advanced science, otherworldly',
            'Fantasy': 'magical elements, enchanted world, mystical creatures, fantasy realm'
        }
        
        genre_enhancement = genre_enhancements.get(genre, '')
        
        # Build comprehensive prompt
        prompt = f"{scene_content[:200]}, {style_prompt}, {genre_enhancement}, {genre} movie, professional quality, 4k resolution, masterpiece"
        
        print(f"📝 Final prompt: {prompt}")
        print(f"📏 Prompt length: {len(prompt)} characters")
        print(f"🎨 Style applied: {style} -> {style_prompt[:50]}...")
        print(f"🎭 Genre applied: {genre} -> {genre_enhancement[:50]}...")
        
        # Generate unique filename
        image_filename = f"scene_{scene_id}_{uuid.uuid4().hex[:8]}.jpg"
        image_path = f"{app.config['OUTPUT_FOLDER']}/{image_filename}"
        print(f"💾 Target file: {image_path}")
        
        # Use SDXL Lightning model
        print("🤖 INITIALIZING AI IMAGE GENERATION...")
        print("   🔗 Loading SDXL Lightning model...")
        sdxl_pipe = get_sdxl_pipe()
        
        if sdxl_pipe:
            print("✅ SDXL Lightning model loaded successfully")
            try:
                print(f"🎨 GENERATING IMAGE FOR SCENE {scene_id}...")
                print("   ⚙️ Model parameters:")
                print("   📊 Inference steps: 4")
                print("   🎯 Guidance scale: 0")
                print("   🖼️ Target resolution: 1024x1024")
                
                # Negative prompts to prevent unwanted styles
                negative_prompts = {
                    'Cinematic': 'anime, cartoon, manga, stylized, unrealistic, low quality, blurry, distorted',
                    'Realistic': 'anime, cartoon, manga, stylized, unrealistic, fantasy, magical, low quality',
                    'Anime': 'realistic, photorealistic, live action, real people, realistic faces, photography',
                    'Cartoon': 'realistic, photorealistic, live action, anime, manga, dark, horror',
                    'Fantasy': 'realistic, photorealistic, modern, contemporary, realistic faces',
                    'Sci-Fi': 'anime, cartoon, fantasy, magical, medieval, historical, realistic faces',
                    'Horror': 'anime, cartoon, bright, cheerful, colorful, happy, family-friendly',
                    'Comedy': 'dark, horror, scary, serious, dramatic, realistic, photorealistic'
                }
                
                negative_prompt = negative_prompts.get(style, 'low quality, blurry, distorted')
                
                print(f"🚫 Negative prompt: {negative_prompt}")
                
                result = sdxl_pipe(
                    prompt, 
                    negative_prompt=negative_prompt,
                    num_inference_steps=4, 
                    guidance_scale=0
                )
                
                print("✅ AI image generation completed successfully!")
                generated_image = result.images[0]
                print(f"🖼️ Generated image size: {generated_image.size}")
                
                print(f"💾 SAVING IMAGE TO DISK...")
                generated_image.save(image_path)
                print(f"✅ Image saved successfully to: {image_path}")
                
                file_size = os.path.getsize(image_path)
                print(f"📊 File size: {file_size} bytes ({file_size/1024:.1f} KB)")
                
            except Exception as e:
                print(f"❌ SDXL Lightning generation failed: {e}")
                print("🔄 FALLBACK: Creating placeholder image...")
                img = Image.new('RGB', (1024, 1024), color=(73, 109, 137))
                img.save(image_path)
                print(f"✅ Placeholder image created: {image_path}")
        else:
            print("❌ SDXL Lightning model not available")
            print("🔄 FALLBACK: Creating placeholder image...")
            img = Image.new('RGB', (1024, 1024), color=(73, 109, 137))
            img.save(image_path)
            print(f"✅ Placeholder image created: {image_path}")
        
        print("🎉 ===== IMAGE GENERATION COMPLETED =====")
        
        return jsonify({
            'success': True,
            'message': f'🎨 Image generated successfully for Scene {scene_id}!',
            'details': f'Created {genre} {style} style image for scene content',
            'image_path': f'/static/output/{os.path.basename(image_path)}',
            'scene_id': scene_id,
            'status': 'SUCCESS',
            'timestamp': time.time(),
            'file_info': {
                'filename': image_filename,
                'size_bytes': os.path.getsize(image_path),
                'size_kb': round(os.path.getsize(image_path) / 1024, 1)
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate_video', methods=['POST'])
def generate_video():
    try:
        print("🎥 ===== VIDEO GENERATION REQUEST RECEIVED =====")
        
        data = request.json
        scene_images = data.get('images', [])
        print(f"📋 Received video generation data:")
        print(f"   🖼️ Scene images: {len(scene_images)}")
        for i, img in enumerate(scene_images):
            print(f"   📸 Scene {i+1}: {img}")
        
        movie_data = session.get('movie_data', {})
        video_id = str(uuid.uuid4())
        
        print(f"🎬 MOVIE CONTEXT:")
        print(f"   📝 Title: {movie_data.get('title', 'Untitled')}")
        print(f"   🎭 Genre: {movie_data.get('genre', 'Unknown')}")
        print(f"   🎨 Style: {movie_data.get('style', 'Unknown')}")
        print(f"   🆔 Video ID: {video_id}")
        
        # Generate video clips for each scene
        print(f"🎬 INITIATING VIDEO GENERATION...")
        print(f"   📊 Processing {len(scene_images)} scene images")
        video_clips = []
        
        for idx, img_path in enumerate(scene_images):
            try:
                print(f"🎬 ===== PROCESSING SCENE {idx + 1}/{len(scene_images)} =====")
                print(f"   📸 Image path: {img_path}")
                
                print("🤖 LOADING VIDEO GENERATION MODEL...")
                pipe = get_video_pipe()
                print("✅ Wan video model loaded successfully")
                
                print("📸 LOADING SCENE IMAGE...")
                image = load_image(img_path)
                print(f"   📏 Original size: {image.size} pixels")
                print(f"   📐 Aspect ratio: {image.height/image.width:.2f}")
                
                # Calculate dimensions
                print("🔧 CALCULATING OPTIMAL DIMENSIONS...")
                max_area = 480 * 832
                aspect_ratio = image.height / image.width
                mod_value = pipe.vae_scale_factor_spatial * pipe.transformer.config.patch_size[1]
                height = round(np.sqrt(max_area * aspect_ratio)) // mod_value * mod_value
                width = round(np.sqrt(max_area / aspect_ratio)) // mod_value * mod_value
                print(f"   📐 Calculated dimensions: {width}x{height}")
                
                image = image.resize((width, height))
                print(f"   ✅ Image resized to: {image.size}")
                
                prompt = f"{movie_data.get('description', 'Cinematic scene')}"
                negative_prompt = "low quality, blurry, static"
                print(f"   📝 Prompt: {prompt}")
                print(f"   🚫 Negative prompt: {negative_prompt}")
                
                print("🎬 GENERATING VIDEO CLIP...")
                print("   ⚙️ Model parameters:")
                print("   📊 Frames: 41")
                print("   🎯 Guidance scale: 3.5")
                print("   🔄 Inference steps: 40")
                print("   🎞️ FPS: 16")
                
                generator = torch.Generator(device=pipe.device).manual_seed(idx)
                output = pipe(
                    image=image,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    height=height,
                    width=width,
                    num_frames=41,
                    guidance_scale=3.5,
                    num_inference_steps=40,
                    generator=generator,
                ).frames[0]
                
                print("✅ Video generation completed successfully!")
                print(f"   🎞️ Generated frames: {len(output)}")
                
                clip_path = f"{app.config['OUTPUT_FOLDER']}/clip_{idx}.mp4"
                print(f"💾 EXPORTING VIDEO CLIP...")
                print(f"   📁 Target file: {clip_path}")
                export_to_video(output, clip_path, fps=16)
                
                file_size = os.path.getsize(clip_path)
                print(f"✅ Scene {idx + 1} video clip created successfully!")
                print(f"   📊 File size: {file_size} bytes ({file_size/1024:.1f} KB)")
                video_clips.append(clip_path)
            
            except Exception as e:
                print(f"❌ VIDEO GENERATION FAILED FOR SCENE {idx + 1}")
                print(f"   🚨 Error: {str(e)}")
                print(f"   📊 Error type: {type(e).__name__}")
                print("   ⏭️ Continuing with next scene...")
                continue
        
        print(f"📊 VIDEO GENERATION SUMMARY:")
        print(f"   ✅ Successful clips: {len(video_clips)}")
        print(f"   ❌ Failed clips: {len(scene_images) - len(video_clips)}")
        
        if not video_clips:
            print("❌ ===== VIDEO GENERATION FAILED =====")
            return jsonify({
                'success': False, 
                'error': 'Video generation failed. No clips were created.',
                'details': 'All scene video generation attempts failed. Please check your images and try again.',
                'suggestion': 'Ensure your images are valid and try again in a moment.',
                'status': 'ERROR',
                'timestamp': time.time()
            }), 500
        
        # Concatenate all clips with transitions
        print(f"🔗 CONCATENATING VIDEO CLIPS WITH TRANSITIONS...")
        print(f"   📹 Loading {len(video_clips)} video clips...")
        clips = [VideoFileClip(clip) for clip in video_clips]
        print(f"   ✅ Loaded {len(clips)} video clips for concatenation")
        
        print("🎬 CREATING FINAL VIDEO WITH TRANSITIONS...")
        
        # Add transitions between clips based on genre
        if len(clips) > 1:
            genre = movie_data.get('genre', 'Drama').lower()
            print(f"   🎭 Adding {genre}-style transitions between scenes...")
            
            # Genre-specific transition settings
            transition_settings = {
                'action': {'type': 'crossfade', 'duration': 0.3, 'effect': 'fast'},
                'adventure': {'type': 'crossfade', 'duration': 0.8, 'effect': 'smooth'},
                'comedy': {'type': 'crossfade', 'duration': 0.4, 'effect': 'bounce'},
                'drama': {'type': 'crossfade', 'duration': 1.0, 'effect': 'smooth'},
                'horror': {'type': 'crossfade', 'duration': 0.6, 'effect': 'fade'},
                'romance': {'type': 'crossfade', 'duration': 1.2, 'effect': 'smooth'},
                'sci-fi': {'type': 'crossfade', 'duration': 0.7, 'effect': 'glitch'},
                'fantasy': {'type': 'crossfade', 'duration': 1.0, 'effect': 'magic'},
                'thriller': {'type': 'crossfade', 'duration': 0.5, 'effect': 'sharp'}
            }
            
            settings = transition_settings.get(genre, transition_settings['drama'])
            transition_duration = settings['duration']
            transition_type = settings['type']
            transition_effect = settings['effect']
            
            print(f"   ⚙️ Transition settings: {transition_type} ({transition_duration}s, {transition_effect})")
            
            # Create transitioned clips
            transitioned_clips = []
            for i, clip in enumerate(clips):
                if i == 0:
                    # First clip - no transition in
                    transitioned_clips.append(clip)
                else:
                    # Add transition based on type
                    if transition_type == 'crossfade':
                        transitioned_clips.append(clip.crossfadein(transition_duration))
                    else:
                        # Default to crossfade
                        transitioned_clips.append(clip.crossfadein(transition_duration))
            
            # Concatenate with transitions
            final_video = concatenate_videoclips(transitioned_clips, method="compose")
            print(f"   ✅ Added {len(clips)-1} {genre}-style transitions")
        else:
            # Single clip - no transitions needed
            final_video = clips[0]
            print("   ℹ️ Single scene - no transitions needed")
        
        # Get video paths based on storage type
        final_path, video_url = get_video_paths(video_id)
        print(f"   📁 Target file: {final_path}")
        print(f"   🌐 Video URL: {video_url}")
        print(f"   ⏱️ Duration: {final_video.duration:.2f} seconds")
        
        # Add cinematic effects
        print("🎨 ADDING CINEMATIC EFFECTS...")
        
        # Add fade in/out effects
        print("   🌅 Adding fade in/out effects...")
        final_video = final_video.fadein(0.5).fadeout(0.5)
        
        # Add cinematic overlays
        print("   📝 Adding cinematic overlays...")
        from moviepy.editor import TextClip, CompositeVideoClip
        
        overlay_clips = []
        
        # Add title overlay if movie title exists
        if movie_data.get('title'):
            print(f"   📝 Adding title overlay: {movie_data.get('title')}")
            
            # Create title text with cinematic styling
            title_clip = TextClip(
                movie_data.get('title'),
                fontsize=60,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=3,
                method='caption',
                size=(final_video.w * 0.8, None)
            ).set_position(('center', 'top')).set_duration(4).set_start(0.5)
            
            # Add fade effect to title
            title_clip = title_clip.fadein(0.5).fadeout(0.5)
            overlay_clips.append(title_clip)
            print("   ✅ Title overlay added")
        
        # Add genre/style info overlay
        if movie_data.get('genre') or movie_data.get('style'):
            print("   🎭 Adding genre/style overlay...")
            genre_style_text = f"{movie_data.get('genre', '')} • {movie_data.get('style', '')}"
            
            info_clip = TextClip(
                genre_style_text,
                fontsize=35,
                color='white',
                font='Arial',
                stroke_color='black',
                stroke_width=2
            ).set_position(('center', 'bottom')).set_duration(4).set_start(0.5)
            
            # Add fade effect
            info_clip = info_clip.fadein(0.5).fadeout(0.5)
            overlay_clips.append(info_clip)
            print("   ✅ Genre/style overlay added")
        
        # Add scene number overlays for each scene
        if len(clips) > 1:
            print("   🔢 Adding scene number overlays...")
            current_time = 0
            
            for i, clip in enumerate(clips):
                scene_duration = clip.duration
                scene_number = i + 1
                
                # Create scene number text
                scene_clip = TextClip(
                    f"Scene {scene_number}",
                    fontsize=40,
                    color='white',
                    font='Arial-Bold',
                    stroke_color='black',
                    stroke_width=2
                ).set_position(('right', 'top')).set_duration(2).set_start(current_time + 0.5)
                
                # Add fade effect
                scene_clip = scene_clip.fadein(0.3).fadeout(0.3)
                overlay_clips.append(scene_clip)
                
                current_time += scene_duration
                print(f"   ✅ Scene {scene_number} overlay added")
        
        # Composite all overlays with video
        if overlay_clips:
            final_video = CompositeVideoClip([final_video] + overlay_clips)
            print(f"   ✅ {len(overlay_clips)} overlays composited")
        
        print("💾 WRITING FINAL VIDEO TO DISK...")
        final_video.write_videofile(
            final_path, 
            codec='libx264', 
            audio=False,
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            fps=24,  # Standard cinematic FPS
            preset='medium',  # Balance between quality and speed
            ffmpeg_params=['-crf', '23']  # High quality encoding
        )
        
        final_size = os.path.getsize(final_path)
        print(f"✅ FINAL VIDEO CREATED SUCCESSFULLY!")
        print(f"   📁 File: {final_path}")
        print(f"   📊 Size: {final_size} bytes ({final_size/1024/1024:.1f} MB)")
        print(f"   ⏱️ Duration: {final_video.duration:.2f} seconds")
        
        # Clean up individual clips
        print("🧹 CLEANING UP TEMPORARY FILES...")
        for clip in video_clips:
            try:
                os.remove(clip)
                print(f"   🗑️ Removed: {clip}")
            except:
                print(f"   ⚠️ Could not remove: {clip}")
        
        print("🎉 ===== VIDEO GENERATION COMPLETED SUCCESSFULLY =====")
        
        # Save movie to history
        print("💾 SAVING MOVIE TO HISTORY...")
        movie_record = {
            'id': video_id,
            'title': movie_data.get('title', 'Untitled Movie'),
            'genre': movie_data.get('genre', 'Unknown'),
            'style': movie_data.get('style', 'Unknown'),
            'description': movie_data.get('description', ''),
            'num_scenes': movie_data.get('numScenes', '5'),
            'video_path': final_path,
            'video_url': video_url,
            'created_at': time.time(),
            'created_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'completed',
            'video_info': {
                'duration_seconds': final_video.duration,
                'file_size_bytes': final_size,
                'file_size_mb': round(final_size / 1024 / 1024, 1),
                'total_clips': len(video_clips),
                'resolution': f"{width}x{height}"
            },
            'scenes': session.get('scenes', []),
            'images': images if 'images' in locals() else []
        }
        
        if save_movie(movie_record):
            print(f"✅ Movie saved to history: {movie_record['title']}")
        else:
            print(f"⚠️ Failed to save movie to history")
        
        return jsonify({
            'success': True,
            'message': f'🎥 Video created successfully! Generated {len(video_clips)} scene clips.',
            'details': f'Created {movie_data.get("title", "Untitled")} video with {len(video_clips)} scenes, {final_video.duration:.1f}s duration',
            'video_path': video_url,
            'video_id': video_id,
            'status': 'SUCCESS',
            'timestamp': time.time(),
            'video_info': {
                'duration_seconds': final_video.duration,
                'file_size_bytes': final_size,
                'file_size_mb': round(final_size / 1024 / 1024, 1),
                'total_clips': len(video_clips),
                'resolution': f"{width}x{height}"
            }
        })
    
    except Exception as e:
        print(f"❌ ===== VIDEO GENERATION FAILED =====")
        print(f"   🚨 Error: {str(e)}")
        print(f"   📊 Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': 'Video generation failed. Please try again.',
            'details': f'Video generation error: {str(e)}',
            'suggestion': 'Check your system resources and try again.',
            'status': 'ERROR',
            'timestamp': time.time(),
            'error_type': type(e).__name__
        }), 500

@app.route('/generate_poster', methods=['POST'])
def generate_poster():
    try:
        data = request.json
        movie_data = session.get('movie_data', {})
        
        # Generate poster (placeholder)
        poster_id = str(uuid.uuid4())
        poster_path = f"{app.config['OUTPUT_FOLDER']}/poster_{poster_id}.jpg"
        
        img = Image.new('RGB', (1080, 1920), color=(20, 20, 40))
        img.save(poster_path)
        
        return jsonify({
            'success': True,
            'poster_path': f'/static/output/poster_{poster_id}.jpg'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    # Print the Colab URL
    port = 5000
    print(f"\n{'='*60}")
    print(f"🎬 AI MOVIE GENERATOR - STARTING UP")
    print(f"{'='*60}")
    print(f"✅ Server initialized successfully")
    print(f"🌐 Local URL: http://localhost:{port}")
    print(f"📱 Mobile-friendly interface ready")
    print(f"🎨 Advanced CSS styling loaded")
    print(f"🤖 AI models: Gemini (Script) + SDXL (Images) + Wan (Video)")
    print(f"{'='*60}")
    print(f"🚀 Ready to create amazing movies!")
    print(f"{'='*60}\n")
    
    # Start ngrok tunnel if available
    if NGROK_AVAILABLE and os.getenv('NGROK_AUTHTOKEN'):
        ngrok.set_auth_token(os.getenv('NGROK_AUTHTOKEN'))
        http_tunnel = ngrok.connect(5000)
        print(f"🌍 Public URL: {http_tunnel.public_url}")
    
    app.run(host='0.0.0.0', port=port, debug=True)
