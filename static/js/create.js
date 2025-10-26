let currentStep = 1;
let movieData = {};
let scenes = [];
let images = [];
let videoPath = '';

function showStep(stepNumber) {
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
    });
    document.getElementById(`step${stepNumber}`).classList.add('active');
    currentStep = stepNumber;
}

function nextStep() {
    if (currentStep === 1) {
        generateScript();
    }
}

async function generateScript() {
    const title = document.getElementById('movieTitle').value;
    const genre = document.getElementById('movieGenre').value;
    const description = document.getElementById('movieDescription').value;
    const style = document.getElementById('movieStyle').value;
    
    movieData = { title, genre, description, style };
    
    try {
        const response = await fetch('/generate_script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(movieData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            scenes = data.scenes;
            displayScript(data.script);
            showStep(2);
        } else {
            alert('Error generating script: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function displayScript(scriptText) {
    const container = document.getElementById('scriptContainer');
    container.innerHTML = `<pre>${scriptText}</pre>`;
}

function regenerateScript() {
    showStep(1);
}

function approveScript() {
    showStep(3);
    generateImages();
}

async function generateImages() {
    const container = document.getElementById('imagesContainer');
    const progressText = document.getElementById('progressText');
    const progressFill = document.getElementById('progressFill');
    
    for (let i = 0; i < scenes.length; i++) {
        progressText.textContent = `Generating image ${i + 1} of ${scenes.length}...`;
        progressFill.style.width = `${((i + 1) / scenes.length) * 100}%`;
        
        try {
            const response = await fetch('/generate_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    scene_id: scenes[i].id,
                    scene_content: scenes[i].content
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                images.push(data.image_path);
                
                // Display image with buttons
                const imageItem = document.createElement('div');
                imageItem.className = 'image-item';
                imageItem.innerHTML = `
                    <img src="${data.image_path}" alt="Scene ${scenes[i].id}" />
                    <div class="image-buttons">
                        <button class="btn-secondary" onclick="regenerateImage(${i})">Regenerate</button>
                        <button class="btn-primary" onclick="approveImage(${i})">Approve</button>
                    </div>
                `;
                container.appendChild(imageItem);
            }
        } catch (error) {
            console.error('Error generating image:', error);
        }
    }
    
    progressText.textContent = 'All images generated!';
    
    // Show button to proceed
    const proceedBtn = document.createElement('button');
    proceedBtn.className = 'btn-primary';
    proceedBtn.textContent = 'Proceed to Video Generation';
    proceedBtn.onclick = () => {
        showStep(4);
        generateVideo();
    };
    container.appendChild(proceedBtn);
}

function regenerateImage(index) {
    // Regenerate specific image
    alert('Regenerating image...');
}

function approveImage(index) {
    // Mark image as approved
    console.log('Image approved:', index);
}

async function generateVideo() {
    const progressBar = document.getElementById('videoProgress');
    
    try {
        const response = await fetch('/generate_video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                images: images
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            videoPath = data.video_path;
            progressBar.style.width = '100%';
            showStep(5);
            displayVideo();
        } else {
            alert('Error generating video: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function displayVideo() {
    const container = document.getElementById('finalVideo');
    container.innerHTML = `<video controls><source src="${videoPath}" type="video/mp4"></video>`;
}

async function generatePoster() {
    try {
        const response = await fetch('/generate_poster', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Poster generated! Click to download.');
            window.open(data.poster_path, '_blank');
        }
    } catch (error) {
        alert('Error generating poster: ' + error.message);
    }
}

function downloadVideo() {
    if (videoPath) {
        window.open(videoPath, '_blank');
    }
}

function shareMovie() {
    if (navigator.share && videoPath) {
        navigator.share({
            title: movieData.title,
            text: 'Check out my AI-generated movie!',
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href);
        alert('Link copied to clipboard!');
    }
}
