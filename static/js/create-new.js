// ========================================
// FUTURISTIC AI MOVIE GENERATOR - JS
// ========================================

let currentStep = 1;
let currentSection = 'Details';
let movieData = {};
let scenes = [];
let images = [];
let videoPath = '';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Ensure only step 1 is visible on load
    showStep(1);
    updateProgress();
    setupCharacterCounter();
    setupButtonListeners();
    setupKeyboardNavigation();
    setupDropdownEnhancements();
    setupStickyElements();
});

// Setup keyboard navigation
function setupKeyboardNavigation() {
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && currentSection === 'Details') {
            e.preventDefault();
            nextStep();
        }
    });
}

// Setup dropdown enhancements
function setupDropdownEnhancements() {
    // Initialize custom dropdowns
    initCustomDropdown('genreDropdown', 'genreTrigger', 'genreMenu', 'movieGenre');
    initCustomDropdown('styleDropdown', 'styleTrigger', 'styleMenu', 'movieStyle');
}

// Initialize custom dropdown
function initCustomDropdown(dropdownId, triggerId, menuId, hiddenInputId) {
    const dropdown = document.getElementById(dropdownId);
    const trigger = document.getElementById(triggerId);
    const menu = document.getElementById(menuId);
    const options = menu.querySelectorAll('.dropdown-option');
    
    // Create hidden input for form submission
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.id = hiddenInputId;
    hiddenInput.name = hiddenInputId;
    dropdown.appendChild(hiddenInput);
    
    // Toggle dropdown
    trigger.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Close other dropdowns
        document.querySelectorAll('.custom-select').forEach(select => {
            if (select !== dropdown) {
                select.classList.remove('open');
            }
        });
        
        dropdown.classList.toggle('open');
        
        if (dropdown.classList.contains('open')) {
            // Hide AI Model Information and Nav Buttons when dropdown opens
            hideModelInfo();
            hideNavButtons();
            // Add particle effect
            createParticleEffect(dropdown);
        } else {
            // Show AI Model Information and Nav Buttons when dropdown closes
            showModelInfo();
            showNavButtons();
        }
    });
    
    // Handle option selection
    options.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const value = this.getAttribute('data-value');
            const text = this.textContent;
            
            // Update trigger text
            const selectedValue = trigger.querySelector('.selected-value');
            selectedValue.textContent = text;
            selectedValue.classList.remove('placeholder');
            
            // Update hidden input
            hiddenInput.value = value;
            
            // Update option states
            options.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            
            // Close dropdown
            dropdown.classList.remove('open');
            
            // Show AI Model Information and Nav Buttons when dropdown closes
            showModelInfo();
            showNavButtons();
            
            // Add success animation
            createSuccessAnimation(dropdown);
            
            // Trigger change event for validation
            hiddenInput.dispatchEvent(new Event('change'));
        });
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!dropdown.contains(e.target)) {
            dropdown.classList.remove('open');
            // Show AI Model Information and Nav Buttons when dropdown closes
            showModelInfo();
            showNavButtons();
        }
    });
    
    // Handle keyboard navigation
    trigger.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            dropdown.classList.toggle('open');
        } else if (e.key === 'Escape') {
            dropdown.classList.remove('open');
        }
    });
    
    // Add hover effects
    trigger.addEventListener('mouseenter', function() {
        dropdown.classList.add('hovered');
    });
    
    trigger.addEventListener('mouseleave', function() {
        dropdown.classList.remove('hovered');
    });
}

// Create particle effect for dropdowns
function createParticleEffect(element) {
    for (let i = 0; i < 6; i++) {
        const particle = document.createElement('div');
        particle.className = 'dropdown-particle';
        particle.style.cssText = `
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--primary);
            border-radius: 50%;
            pointer-events: none;
            z-index: 1000;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: particleFloat 1.5s ease-out forwards;
        `;
        element.appendChild(particle);
        
        setTimeout(() => {
            particle.remove();
        }, 1500);
    }
}

// Create success animation
function createSuccessAnimation(element) {
    const checkmark = document.createElement('div');
    checkmark.innerHTML = '✓';
    checkmark.style.cssText = `
        position: absolute;
        right: 3rem;
        top: 50%;
        transform: translateY(-50%) scale(0);
        color: var(--success);
        font-size: 1.2rem;
        font-weight: bold;
        z-index: 1000;
        animation: checkmarkPop 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
    `;
    element.appendChild(checkmark);
    
    setTimeout(() => {
        checkmark.remove();
    }, 1000);
}

// Setup sticky elements
function setupStickyElements() {
    const topNav = document.querySelector('.top-nav');
    
    // Ensure proper z-index stacking for header only
    if (topNav) {
        topNav.style.zIndex = '2000';
    }
    
    // Handle scroll events to maintain sticky behavior for header only
    let lastScrollTop = 0;
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add shadow to nav when scrolling
        if (topNav) {
            if (scrollTop > 10) {
                topNav.style.boxShadow = '0 8px 30px rgba(0, 0, 0, 0.3)';
            } else {
                topNav.style.boxShadow = 'var(--shadow-sm)';
            }
        }
        
        // Ensure header stays in place
        if (topNav) {
            topNav.style.position = 'fixed';
            topNav.style.top = '0';
            topNav.style.left = '0';
            topNav.style.right = '0';
        }
        
        lastScrollTop = scrollTop;
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        // Recalculate positions on resize for header only
        if (topNav) {
            topNav.style.top = '0';
        }
    });
}

// Setup all button event listeners
function setupButtonListeners() {
    // Navigation buttons
    const nextButtons = document.querySelectorAll('.btn-next');
    const prevButtons = document.querySelectorAll('.btn-previous');
    const primaryButtons = document.querySelectorAll('.btn-primary');
    
    nextButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            nextStep();
        });
    });
    
    prevButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            prevStep();
        });
    });
    
    primaryButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (btn.textContent.includes('Review')) {
                showReview();
            } else if (btn.textContent.includes('Generate Script')) {
                generateScript();
            }
        });
    });
    
    // Scene selection buttons
    const sceneCards = document.querySelectorAll('.scene-card');
    sceneCards.forEach(card => {
        card.addEventListener('click', function(e) {
            e.preventDefault();
            const sceneNumber = this.querySelector('.scene-number').textContent;
            selectScenes(parseInt(sceneNumber));
        });
    });
    
    // Add button responsiveness
    const allButtons = document.querySelectorAll('.btn-nav, .btn-primary, .scene-card');
    allButtons.forEach(button => {
        // Add ripple effect
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
                z-index: 1000;
            `;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
        
        // Touch feedback
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

// Character counter
function setupCharacterCounter() {
    const desc = document.getElementById('movieDescription');
    if (desc) {
        desc.addEventListener('input', function() {
            const charCount = this.value.length;
            document.getElementById('charCount').textContent = charCount;
        });
    }
}

// Update progress indicators
function updateProgress() {
    let sectionIndex = 1;
    
    if (currentSection === 'Details') {
        sectionIndex = 1;
    } else if (currentSection === 'Script') {
        sectionIndex = 2;
    } else if (currentSection === 'Images') {
        sectionIndex = 3;
    } else if (currentSection === 'Video') {
        sectionIndex = 4;
    } else if (currentSection === 'Result') {
        sectionIndex = 5;
    }
    
    // Update step indicators with animations
    document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
        const stepNumber = index + 1;
        
        // Remove all states
        indicator.classList.remove('active', 'completed');
        
        if (stepNumber < sectionIndex) {
            // Completed steps - add with delay for animation
            setTimeout(() => {
                indicator.classList.add('completed');
            }, index * 100);
        } else if (stepNumber === sectionIndex) {
            // Current step
            indicator.classList.add('active');
        }
    });
    
    // Update connectors with animation
    document.querySelectorAll('.step-connector').forEach((connector, index) => {
        const stepNumber = index + 1;
        
        // Remove completed class
        connector.classList.remove('completed');
        
        // Add completed class if this connector leads to a completed step
        if (stepNumber < sectionIndex) {
            setTimeout(() => {
                connector.classList.add('completed');
            }, (index + 1) * 150);
        }
    });
    
    // Calculate percentage with animation
    let percentage = 0;
    if (sectionIndex === 1) {
        percentage = (currentStep / 6) * 20;
    } else if (sectionIndex === 2) {
        percentage = 20 + 20;
    } else if (sectionIndex === 3) {
        percentage = 40 + 20;
    } else if (sectionIndex === 4) {
        percentage = 60 + 20;
    } else if (sectionIndex === 5) {
        percentage = 100;
    }
    
    // Animate percentage change
    const progressElement = document.getElementById('progressPercent');
    if (progressElement) {
        let currentPercent = 0;
        const targetPercent = Math.round(percentage);
        const increment = targetPercent / 20; // 20 steps for smooth animation
        
        const animatePercent = () => {
            if (currentPercent < targetPercent) {
                currentPercent += increment;
                progressElement.textContent = Math.round(currentPercent) + '%';
                requestAnimationFrame(animatePercent);
            } else {
                progressElement.textContent = targetPercent + '%';
            }
        };
        
        animatePercent();
    }
}

// Step navigation
function showStep(stepNumber) {
    console.log(`Showing step ${stepNumber}`);
    
    // Hide all steps with smooth transition
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active');
        console.log(`Step ${index + 1} hidden`);
    });
    
    // Show the target step with a slight delay for smooth transition
    setTimeout(() => {
        const stepElement = document.getElementById(`step${stepNumber}`);
        if (stepElement) {
            stepElement.classList.add('active');
            currentStep = stepNumber;
            updateProgress();
            console.log(`Step ${stepNumber} is now active`);
            
            // Focus on the first input in the step
            const firstInput = stepElement.querySelector('input, textarea, select');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        } else {
            console.error(`Step ${stepNumber} element not found`);
        }
    }, 200);
}

function nextStep() {
    // Validate current step before proceeding
    if (validateCurrentStep()) {
        if (currentStep < 6) {
            showStep(currentStep + 1);
        }
    }
}

// Validate current step
function validateCurrentStep() {
    switch (currentStep) {
        case 1: // Movie Title
            const title = document.getElementById('movieTitle').value.trim();
            if (!title) {
                alert('Please enter a movie title before proceeding.');
                return false;
            }
            break;
        case 2: // Genre
            const genre = document.getElementById('movieGenre').value;
            if (!genre) {
                alert('Please select a genre before proceeding.');
                return false;
            }
            break;
        case 3: // Description
            const description = document.getElementById('movieDescription').value.trim();
            if (!description) {
                alert('Please enter a movie description before proceeding.');
                return false;
            }
            break;
        case 4: // Style
            const style = document.getElementById('movieStyle').value;
            if (!style) {
                alert('Please select a visual style before proceeding.');
                return false;
            }
            break;
        case 5: // Number of scenes (already has default selection)
            // No validation needed as there's a default selection
            break;
    }
    return true;
}

function prevStep() {
    if (currentStep > 1) {
        showStep(currentStep - 1);
    }
}

// Show sections
function showSection(sectionName) {
    // Hide all sections with smooth transition
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show the target section with a slight delay for smooth transition
    setTimeout(() => {
        const sectionElement = document.getElementById(`section${sectionName}`);
        if (sectionElement) {
            sectionElement.classList.add('active');
            currentSection = sectionName;
            updateProgress();
        }
    }, 300);
}

// Select number of scenes
function selectScenes(count, element) {
    document.querySelectorAll('.scene-card').forEach(card => {
        card.classList.remove('active');
    });
    element.classList.add('active');
    document.getElementById('numScenes').value = count;
    console.log(`Selected ${count} scenes`);
}

// Show review
function showReview() {
    const title = document.getElementById('movieTitle').value;
    const genre = document.getElementById('movieGenre').value;
    const description = document.getElementById('movieDescription').value;
    const style = document.getElementById('movieStyle').value;
    const numScenes = document.getElementById('numScenes').value;

    const container = document.getElementById('reviewContainer');
    container.innerHTML = `
        <div class="review-item">
            <div class="review-label">Movie Title</div>
            <div class="review-value">${title || 'Not specified'}</div>
        </div>
        <div class="review-item">
            <div class="review-label">Genre</div>
            <div class="review-value">${genre || 'Not specified'}</div>
        </div>
        <div class="review-item">
            <div class="review-label">Description</div>
            <div class="review-value">${description.substring(0, 100)}${description.length > 100 ? '...' : ''}</div>
        </div>
        <div class="review-item">
            <div class="review-label">Visual Style</div>
            <div class="review-value">${style || 'Not specified'}</div>
        </div>
        <div class="review-item">
            <div class="review-label">Number of Scenes</div>
            <div class="review-value">${numScenes || 'Not specified'}</div>
        </div>
    `;

    showStep(6);
}

// Generate script
async function generateScript() {
    const title = document.getElementById('movieTitle').value;
    const genre = document.getElementById('movieGenre').value;
    const description = document.getElementById('movieDescription').value;
    const style = document.getElementById('movieStyle').value;
    const numScenes = document.getElementById('numScenes').value;
    
    movieData = { title, genre, description, style, numScenes };
    
    // Switch to Script section
    showSection('Script');
    
    // Update script generation UI
    const scriptProgress = document.getElementById('scriptProgress');
    const scriptGenSubtitle = document.getElementById('scriptGenSubtitle');
    
    let progressPercent = 0;
    const progressInterval = setInterval(() => {
        progressPercent += 2;
        scriptProgress.style.width = progressPercent + '%';
        if (progressPercent >= 90) {
            clearInterval(progressInterval);
        }
    }, 100);
    
    try {
        const response = await fetch('/generate_script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(movieData)
        });
        
        const data = await response.json();
        clearInterval(progressInterval);
        scriptProgress.style.width = '100%';
        
        if (data.success) {
            scenes = data.scenes;
            console.log(`✅ Script generation successful!`);
            console.log(`📊 Received ${scenes.length} scenes:`, scenes);
            console.log(`📄 Script length: ${data.script.length} characters`);
            
            displayScript(data.script);
            
            // Show success message
            if (data.message) {
                scriptGenSubtitle.textContent = data.message;
            }
            
            // Add approve button after delay
            setTimeout(() => {
                const scriptContainer = document.getElementById('scriptContainer');
                const approveBtn = document.createElement('button');
                approveBtn.className = 'btn-nav btn-primary';
                approveBtn.style.marginTop = '2rem';
                approveBtn.style.marginLeft = 'auto';
                approveBtn.style.marginRight = 'auto';
                approveBtn.innerHTML = 'Approve & Generate Images <span>→</span>';
                approveBtn.onclick = approveScript;
                scriptContainer.appendChild(approveBtn);
            }, 1000);
        } else {
            document.getElementById('scriptGenTitle').textContent = 'Script Generation Failed';
            let errorMsg = data.error || 'Unknown error occurred';
            if (data.suggestion) {
                errorMsg += '\n\nSuggestion: ' + data.suggestion;
            }
            scriptGenSubtitle.textContent = errorMsg;
        }
    } catch (error) {
        clearInterval(progressInterval);
        document.getElementById('scriptGenTitle').textContent = 'Error Generating Script';
        scriptGenSubtitle.textContent = 'Error: ' + error.message;
    }
}

// Display script
function displayScript(scriptText) {
    console.log(`🎬 DISPLAYING SCRIPT...`);
    console.log(`   📊 Scenes to display: ${scenes.length}`);
    console.log(`   📄 Script text length: ${scriptText.length}`);
    
    const container = document.getElementById('scriptContainer');
    
    let html = '<div class="script-display">';
    
    scenes.forEach((scene, index) => {
        console.log(`   📝 Displaying Scene ${index + 1}:`, scene);
        html += `
            <div class="scene-block-new">
                <h3 class="scene-title-new">${scene.title || `Scene ${scene.id}`}</h3>
                <p class="scene-content">${scene.content}</p>
                <div class="scene-meta">
                    <span class="scene-genre">🎬 ${movieData.genre}</span>
                    <span class="scene-style">🎨 ${movieData.style}</span>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    console.log(`✅ Script display completed with ${scenes.length} scenes`);
}

// Regenerate script
function regenerateScript() {
    document.getElementById('scriptContainer').innerHTML = '';
    document.getElementById('scriptGenTitle').textContent = 'Generating Your Script';
    document.getElementById('scriptGenSubtitle').textContent = 'AI is analyzing your concept and creating a professional screenplay...';
    generateScript();
}

// Approve script and go to images
function approveScript() {
    showSection('Images');
    generateImages();
}

// Generate images for each scene
async function generateImages() {
    console.log(`🖼️ GENERATING IMAGES...`);
    console.log(`   📊 Scenes to process: ${scenes.length}`);
    console.log(`   🎬 Movie data:`, movieData);
    
    const container = document.getElementById('imagesContainer');
    container.innerHTML = '';
    
    // Create placeholders for all scenes
    scenes.forEach((scene, index) => {
        console.log(`   📝 Creating placeholder for Scene ${index + 1}:`, scene);
        const sceneCard = document.createElement('div');
        sceneCard.className = 'scene-card-item';
        sceneCard.id = `scene-card-${index}`;
        sceneCard.innerHTML = `
            <div class="scene-header-new">
                <div class="scene-title-new">${scene.title || `Scene ${scene.id}`}</div>
                <div class="scene-number-new">Scene ${scene.id} of ${scenes.length}</div>
            </div>
            <div class="scene-image-placeholder">
                <div class="loading-spinner-large"></div>
                <span class="scene-status status-processing">Processing...</span>
            </div>
            <div class="scene-actions" style="display: none;">
                <button class="btn-scene" onclick="regenerateImage(${index})">🔄 Regenerate</button>
                <button class="btn-scene" onclick="approveImage(${index})">✓ Approve</button>
            </div>
        `;
        container.appendChild(sceneCard);
    });
    
    // Update progress
    const imageProgress = document.getElementById('imageProgress');
    const imageProgressText = document.getElementById('imageProgressText');
    let progressPercent = 0;
    
    // Generate images sequentially
    for (let i = 0; i < scenes.length; i++) {
        imageProgressText.textContent = `Generating image ${i + 1} of ${scenes.length}...`;
        imageProgress.style.width = ((i / scenes.length) * 100) + '%';
        
        try {
            const response = await fetch('/generate_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    scene_id: scenes[i].id,
                    scene_content: scenes[i].content,
                    genre: movieData.genre,
                    style: movieData.style
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                images.push(data.image_path);
                updateSceneCard(i, scenes[i], data.image_path, 'success');
                console.log(data.message || `Scene ${i + 1} image generated successfully`);
            } else {
                let errorMsg = data.error || 'Image generation failed';
                if (data.suggestion) {
                    errorMsg += ' - ' + data.suggestion;
                }
                updateSceneCard(i, scenes[i], null, 'error', errorMsg);
            }
        } catch (error) {
            updateSceneCard(i, scenes[i], null, 'error', error.message);
        }
    }
    
    // Final progress
    imageProgress.style.width = '100%';
    imageProgressText.textContent = '✓ All images generated successfully!';
    
    // Add proceed button
    setTimeout(() => {
        const proceedBtn = document.createElement('button');
        proceedBtn.className = 'btn-nav btn-primary';
        proceedBtn.style.margin = '2rem auto';
        proceedBtn.style.display = 'block';
        proceedBtn.textContent = 'Proceed to Video Generation →';
        proceedBtn.onclick = () => {
            showSection('Video');
            generateVideo();
        };
        container.appendChild(proceedBtn);
    }, 1000);
}

// Update scene card
function updateSceneCard(index, scene, imagePath, status, error = null) {
    const card = document.getElementById(`scene-card-${index}`);
    
    if (status === 'success') {
        card.innerHTML = `
            <div class="scene-header-new">
                <div class="scene-title-new">${scene.title || `Scene ${scene.id}`}</div>
                <div class="scene-number-new">Scene ${scene.id} of ${scenes.length}</div>
            </div>
            <img src="${imagePath}" alt="Scene ${scene.id}" class="scene-image" />
            <div class="scene-actions">
                <button class="btn-scene" onclick="regenerateImage(${index})">🔄 Regenerate</button>
                <button class="btn-scene" onclick="approveImage(${index})">✓ Approve</button>
            </div>
        `;
    } else {
        card.innerHTML = `
            <div class="scene-header-new">
                <div class="scene-title-new">${scene.title || `Scene ${scene.id}`}</div>
                <div class="scene-number-new">Scene ${scene.id} of ${scenes.length}</div>
            </div>
            <div class="scene-image-placeholder">
                <span class="scene-status status-error">Error: ${error}</span>
            </div>
            <div class="scene-actions">
                <button class="btn-scene" onclick="regenerateImage(${index})">🔄 Try Again</button>
            </div>
        `;
    }
}

// Regenerate single image
async function regenerateImage(index) {
    const card = document.getElementById(`scene-card-${index}`);
    card.innerHTML = `
        <div class="scene-header-new">
            <div class="scene-title-new">${scenes[index].title || `Scene ${scenes[index].id}`}</div>
            <div class="scene-number-new">Scene ${scenes[index].id} of ${scenes.length}</div>
        </div>
        <div class="scene-image-placeholder">
            <div class="loading-spinner-large"></div>
            <span class="scene-status status-processing">Regenerating...</span>
        </div>
    `;
    
    try {
        const response = await fetch('/generate_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scene_id: scenes[index].id,
                scene_content: scenes[index].content,
                genre: movieData.genre,
                style: movieData.style
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            images[index] = data.image_path;
            updateSceneCard(index, scenes[index], data.image_path, 'success');
        } else {
            updateSceneCard(index, scenes[index], null, 'error', data.error);
        }
    } catch (error) {
        updateSceneCard(index, scenes[index], null, 'error', error.message);
    }
}

function approveImage(index) {
    console.log('Image approved:', index);
}

// Generate video
async function generateVideo() {
    const videoProgress = document.getElementById('videoProgress');
    const videoGenSubtitle = document.getElementById('videoGenSubtitle');
    
    let progressPercent = 0;
    const progressInterval = setInterval(() => {
        progressPercent += 2;
        videoProgress.style.width = progressPercent + '%';
        if (progressPercent >= 90) {
            clearInterval(progressInterval);
        }
    }, 150);
    
    try {
        const response = await fetch('/generate_video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                images: images,
                movie_data: movieData
            })
        });
        
        clearInterval(progressInterval);
        videoProgress.style.width = '100%';
        
        const data = await response.json();
        
        if (data.success) {
            videoPath = data.video_path;
            videoGenSubtitle.textContent = data.message || '✓ Video generation complete!';
            
            setTimeout(() => {
                showSection('Result');
                displayVideo();
            }, 1000);
        } else {
            document.getElementById('scriptGenTitle').textContent = 'Video Generation Failed';
            let errorMsg = data.error || 'Video generation failed';
            if (data.suggestion) {
                errorMsg += '\n\nSuggestion: ' + data.suggestion;
            }
            videoGenSubtitle.textContent = errorMsg;
        }
    } catch (error) {
        clearInterval(progressInterval);
        document.getElementById('scriptGenTitle').textContent = 'Error Generating Video';
        videoGenSubtitle.textContent = 'Error: ' + error.message;
    }
}

// Display video
function displayVideo() {
    const container = document.getElementById('finalVideo');
    container.innerHTML = `
        <video controls autoplay style="max-width: 100%; border-radius: 20px;">
            <source src="${videoPath}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
        <div style="margin-top: 2rem;">
            <h3 style="color: var(--primary); font-size: 2rem;">${movieData.title}</h3>
            <p style="color: var(--text-muted); font-size: 1.1rem;">${movieData.genre} • ${movieData.style}</p>
        </div>
    `;
}

// Other functions
function generatePoster() {
    alert('Poster generation feature coming soon!');
}

function downloadVideo() {
    if (videoPath) {
        const a = document.createElement('a');
        a.href = videoPath;
        a.download = `${movieData.title.replace(/\s+/g, '_')}_${Date.now()}.mp4`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
}

function shareMovie() {
    if (navigator.share && videoPath) {
        navigator.share({
            title: movieData.title || 'My AI Generated Movie',
            text: 'Check out my AI-generated movie!',
            url: window.location.href
        });
    } else {
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            alert('Link copied to clipboard!');
        });
    }
}

// Function to hide AI Model Information
function hideModelInfo() {
    const modelInfoSection = document.querySelector('.model-info-section');
    if (modelInfoSection) {
        modelInfoSection.style.opacity = '0';
        modelInfoSection.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            modelInfoSection.style.display = 'none';
        }, 300);
    }
}

// Function to show AI Model Information
function showModelInfo() {
    const modelInfoSection = document.querySelector('.model-info-section');
    if (modelInfoSection) {
        modelInfoSection.style.display = 'block';
        // Force reflow
        modelInfoSection.offsetHeight;
        modelInfoSection.style.opacity = '1';
        modelInfoSection.style.transform = 'translateY(0)';
    }
}

// Function to hide Nav Buttons
function hideNavButtons() {
    const navButtons = document.querySelector('.nav-buttons');
    console.log('Hiding nav buttons:', navButtons);
    if (navButtons) {
        // Immediate hide
        navButtons.style.display = 'none';
        navButtons.style.visibility = 'hidden';
        navButtons.style.opacity = '0';
        navButtons.style.transform = 'translateY(-10px)';
        navButtons.style.zIndex = '-1';
    }
}

// Function to show Nav Buttons
function showNavButtons() {
    const navButtons = document.querySelector('.nav-buttons');
    console.log('Showing nav buttons:', navButtons);
    if (navButtons) {
        navButtons.style.display = 'flex';
        // Force reflow
        navButtons.offsetHeight;
        navButtons.style.visibility = 'visible';
        navButtons.style.opacity = '1';
        navButtons.style.transform = 'translateY(0)';
        navButtons.style.zIndex = '1';
    }
}

// Function to select genre from grid
function selectGenre(genre, element) {
    console.log('Selecting genre:', genre);
    
    // Remove selected class from all genre options
    document.querySelectorAll('.genre-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    // Add selected class to clicked option
    element.classList.add('selected');
    
    // Update hidden input
    const hiddenInput = document.getElementById('movieGenre');
    if (hiddenInput) {
        hiddenInput.value = genre;
        console.log('Updated movieGenre input to:', genre);
    }
    
    // Trigger change event for validation
    if (hiddenInput) {
        hiddenInput.dispatchEvent(new Event('change'));
    }
}

// Function to select style from grid
function selectStyle(style, element) {
    console.log('Selecting style:', style);
    
    // Remove selected class from all style options
    document.querySelectorAll('.style-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    // Add selected class to clicked option
    element.classList.add('selected');
    
    // Update hidden input
    const hiddenInput = document.getElementById('movieStyle');
    if (hiddenInput) {
        hiddenInput.value = style;
        console.log('Updated movieStyle input to:', style);
    }
    
    // Trigger change event for validation
    if (hiddenInput) {
        hiddenInput.dispatchEvent(new Event('change'));
    }
}
