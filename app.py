from flask import Flask, render_template, request, jsonify, send_file, session
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

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Initialize Gemini client (with error handling)
try:
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if gemini_api_key:
        genai_client = genai.Client(api_key=gemini_api_key)
    else:
        print("Warning: GEMINI_API_KEY not set. Script generation will fail.")
        genai_client = None
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    genai_client = None

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

@app.route('/generate_script', methods=['POST'])
def generate_script():
    try:
        if not genai_client:
            return jsonify({'success': False, 'error': 'Gemini API not configured'}), 500
        
        data = request.json
        title = data.get('title', 'Untitled Movie')
        genre = data.get('genre', 'Action')
        description = data.get('description', '')
        style = data.get('style', 'Cinematic')
        
        # Store in session
        session['movie_data'] = {
            'title': title,
            'genre': genre,
            'description': description,
            'style': style
        }
        
        # Generate script using Gemini
        prompt = f"""Generate a movie script based on the following details:
Title: {title}
Genre: {genre}
Description: {description}
Style: {style}

Please create a script with multiple scenes. Format each scene as:
Scene [number]: [Scene Title]
[Scene description and dialogue]

Make it vivid and engaging, suitable for the {genre} genre and {style} style."""
        
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        
        script = response.text
        
        # Parse script into scenes
        scenes = parse_script_to_scenes(script)
        
        return jsonify({
            'success': True,
            'script': script,
            'scenes': scenes
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def parse_script_to_scenes(script):
    """Parse script text into scene objects"""
    scenes = []
    lines = script.split('\n')
    current_scene = None
    current_content = []
    
    for line in lines:
        if line.strip().startswith('Scene') or line.strip().startswith('SCENE'):
            if current_scene:
                scenes.append({
                    'id': len(scenes) + 1,
                    'title': current_scene,
                    'content': '\n'.join(current_content).strip()
                })
            current_scene = line.strip()
            current_content = []
        else:
            if current_scene:
                current_content.append(line)
    
    if current_scene:
        scenes.append({
            'id': len(scenes) + 1,
            'title': current_scene,
            'content': '\n'.join(current_content).strip()
        })
    
    return scenes if scenes else [{'id': 1, 'title': 'Scene 1', 'content': script}]

@app.route('/generate_image', methods=['POST'])
def generate_image():
    try:
        data = request.json
        scene_id = data.get('scene_id')
        scene_content = data.get('scene_content')
        
        movie_data = session.get('movie_data', {})
        
        # Generate image using FLUX API (placeholder - implement actual FLUX API)
        # For now, using a placeholder image generation
        
        prompt = f"{scene_content[:200]}"
        
        # Simulate image generation
        image_path = f"{app.config['OUTPUT_FOLDER']}/scene_{scene_id}.jpg"
        
        # Placeholder: Create a solid color image
        img = Image.new('RGB', (512, 512), color=(73, 109, 137))
        img.save(image_path)
        
        return jsonify({
            'success': True,
            'image_path': f'/static/output/scene_{scene_id}.jpg',
            'scene_id': scene_id
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate_video', methods=['POST'])
def generate_video():
    try:
        data = request.json
        scene_images = data.get('images', [])
        
        movie_data = session.get('movie_data', {})
        video_id = str(uuid.uuid4())
        
        # Generate video clips for each scene
        video_clips = []
        
        for idx, img_path in enumerate(scene_images):
            try:
                pipe = get_video_pipe()
                image = load_image(img_path)
                
                # Calculate dimensions
                max_area = 480 * 832
                aspect_ratio = image.height / image.width
                mod_value = pipe.vae_scale_factor_spatial * pipe.transformer.config.patch_size[1]
                height = round(np.sqrt(max_area * aspect_ratio)) // mod_value * mod_value
                width = round(np.sqrt(max_area / aspect_ratio)) // mod_value * mod_value
                image = image.resize((width, height))
                
                prompt = f"{movie_data.get('description', 'Cinematic scene')}"
                negative_prompt = "low quality, blurry, static"
                
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
                
                clip_path = f"{app.config['OUTPUT_FOLDER']}/clip_{idx}.mp4"
                export_to_video(output, clip_path, fps=16)
                video_clips.append(clip_path)
            
            except Exception as e:
                print(f"Error generating video for scene {idx}: {e}")
                continue
        
        if not video_clips:
            return jsonify({'success': False, 'error': 'No video clips generated'}), 500
        
        # Concatenate all clips
        clips = [VideoFileClip(clip) for clip in video_clips]
        final_video = concatenate_videoclips(clips)
        final_path = f"{app.config['OUTPUT_FOLDER']}/{video_id}.mp4"
        final_video.write_videofile(final_path, codec='libx264', audio=False)
        
        # Add audio (placeholder - implement ElevenLabs)
        # For now, skip audio
        
        return jsonify({
            'success': True,
            'video_path': f'/static/output/{video_id}.mp4',
            'video_id': video_id
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    # Start ngrok tunnel if available
    if NGROK_AVAILABLE and os.getenv('NGROK_AUTHTOKEN'):
        ngrok.set_auth_token(os.getenv('NGROK_AUTHTOKEN'))
        http_tunnel = ngrok.connect(5000)
        print(f"Ngrok tunnel: {http_tunnel.public_url}")
    else:
        print("Running without ngrok. Access at http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
