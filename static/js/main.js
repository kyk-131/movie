// Landing page animations and interactions
document.addEventListener('DOMContentLoaded', function() {
    // Add floating animation to geometric shapes
    const shapes = document.querySelectorAll('.cube, .sphere, .pyramid, .ring, .triangle');
    
    shapes.forEach(shape => {
        shape.style.animation = `float ${Math.random() * 3 + 2}s ease-in-out infinite`;
    });

    // Enhanced button interactions
    const allButtons = document.querySelectorAll('.btn, .btn-nav, .btn-result, .btn-scene, .cta-button');
    
    allButtons.forEach(button => {
        // Add ripple effect on click
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });

        // Add hover sound effect (visual feedback)
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px) scale(1.02)';
        });

        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });

        // Touch feedback for mobile
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.95)';
        });

        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Initialize video player and testimonials
    initVideoPlayer();
    initTestimonials();
});

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes float {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(10deg); }
    }
    
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .cube, .sphere, .pyramid, .ring, .triangle {
        position: absolute;
        opacity: 0.1;
    }
    
    .cube {
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #00f0ff, #8338ec);
        top: 20%;
        left: 10%;
        animation: float 4s ease-in-out infinite;
        transform: rotate(45deg);
    }
    
    .sphere {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: radial-gradient(circle, #ff006e, #8338ec);
        top: 60%;
        right: 15%;
        animation: float 5s ease-in-out infinite;
    }
    
    .pyramid {
        width: 0;
        height: 0;
        border-left: 30px solid transparent;
        border-right: 30px solid transparent;
        border-bottom: 50px solid #00f0ff;
        bottom: 20%;
        right: 30%;
        animation: float 6s ease-in-out infinite;
    }

    .ring {
        width: 80px;
        height: 80px;
        border: 3px solid #00f0ff;
        border-radius: 50%;
        top: 30%;
        right: 20%;
        animation: float 7s ease-in-out infinite;
    }

    .triangle {
        width: 0;
        height: 0;
        border-left: 25px solid transparent;
        border-right: 25px solid transparent;
        border-bottom: 40px solid #ff006e;
        top: 70%;
        left: 15%;
        animation: float 8s ease-in-out infinite;
    }
`;
document.head.appendChild(style);

// Video Player Functions
function initVideoPlayer() {
    const video = document.getElementById('demoVideo');
    const playButton = document.getElementById('playButton');
    const progressBar = document.querySelector('.progress-bar');
    const progressFill = document.querySelector('.progress-fill');
    const currentTimeEl = document.querySelector('.current-time');
    const durationEl = document.querySelector('.duration');
    const videoOverlay = document.getElementById('videoOverlay');
    
    if (!video || !playButton) return;
    
    let isPlaying = false;
    
    // Try to autoplay the video
    video.play().then(() => {
        // Autoplay successful
        isPlaying = true;
        playButton.innerHTML = '<div class="play-icon">⏸</div>';
        videoOverlay.style.opacity = '0';
    }).catch((error) => {
        // Autoplay failed (browser restrictions)
        console.log('Autoplay prevented:', error);
        isPlaying = false;
        playButton.innerHTML = '<div class="play-icon">▶</div>';
        videoOverlay.style.opacity = '1';
    });
    
    // Play/Pause functionality
    playButton.addEventListener('click', function() {
        if (isPlaying) {
            video.pause();
            playButton.innerHTML = '<div class="play-icon">▶</div>';
            isPlaying = false;
        } else {
            video.play();
            playButton.innerHTML = '<div class="play-icon">⏸</div>';
            isPlaying = true;
            videoOverlay.style.opacity = '0';
        }
    });
    
    // Video event listeners
    video.addEventListener('play', function() {
        isPlaying = true;
        playButton.innerHTML = '<div class="play-icon">⏸</div>';
    });
    
    video.addEventListener('pause', function() {
        isPlaying = false;
        playButton.innerHTML = '<div class="play-icon">▶</div>';
    });
    
    video.addEventListener('ended', function() {
        isPlaying = false;
        playButton.innerHTML = '<div class="play-icon">▶</div>';
        videoOverlay.style.opacity = '1';
    });
    
    // Progress bar functionality
    video.addEventListener('timeupdate', function() {
        if (video.duration) {
            const progress = (video.currentTime / video.duration) * 100;
            progressFill.style.width = progress + '%';
            
            currentTimeEl.textContent = formatTime(video.currentTime);
            durationEl.textContent = formatTime(video.duration);
        }
    });
    
    // Click on progress bar to seek
    progressBar.addEventListener('click', function(e) {
        if (video.duration) {
            const rect = progressBar.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const percentage = clickX / rect.width;
            video.currentTime = percentage * video.duration;
        }
    });
    
    // Hover effects
    const videoPlayer = document.querySelector('.video-player');
    videoPlayer.addEventListener('mouseenter', function() {
        videoOverlay.style.opacity = '1';
    });
    
    videoPlayer.addEventListener('mouseleave', function() {
        if (isPlaying) {
            videoOverlay.style.opacity = '0';
        }
    });
}

// Format time helper
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Testimonials Slider Functions
function initTestimonials() {
    const testimonials = document.querySelectorAll('.testimonial');
    const dots = document.querySelectorAll('.dot');
    let currentSlide = 0;
    
    if (testimonials.length === 0) return;
    
    // Show specific slide
    function showSlide(index) {
        testimonials.forEach((testimonial, i) => {
            testimonial.classList.toggle('active', i === index);
        });
        
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
        
        currentSlide = index;
    }
    
    // Auto-advance slides
    function nextSlide() {
        const next = (currentSlide + 1) % testimonials.length;
        showSlide(next);
    }
    
    // Dot click handlers
    dots.forEach((dot, index) => {
        dot.addEventListener('click', function() {
            showSlide(index);
        });
    });
    
    // Auto-advance every 5 seconds
    setInterval(nextSlide, 5000);
    
    // Initialize first slide
    showSlide(0);
}
