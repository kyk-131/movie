// History page functionality
let movies = [];
let filteredMovies = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadMovies();
    setupEventListeners();
});

// Load movies from API
async function loadMovies() {
    try {
        console.log('📚 Loading movies from history...');
        const response = await fetch('/api/movies');
        const data = await response.json();
        
        if (data.success) {
            movies = data.movies;
            filteredMovies = [...movies];
            console.log(`✅ Loaded ${movies.length} movies`);
            displayMovies();
        } else {
            console.error('❌ Failed to load movies:', data.error);
            showError('Failed to load movies: ' + data.error);
        }
    } catch (error) {
        console.error('❌ Error loading movies:', error);
        showError('Error loading movies: ' + error.message);
    }
}

// Display movies in grid
function displayMovies() {
    const grid = document.getElementById('moviesGrid');
    const emptyState = document.getElementById('emptyState');
    
    if (filteredMovies.length === 0) {
        grid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    grid.style.display = 'grid';
    emptyState.style.display = 'none';
    
    grid.innerHTML = filteredMovies.map(movie => createMovieCard(movie)).join('');
}

// Create movie card HTML
function createMovieCard(movie) {
    const createdDate = new Date(movie.created_at * 1000).toLocaleDateString();
    const duration = movie.video_info ? formatDuration(movie.video_info.duration_seconds) : 'Unknown';
    const fileSize = movie.video_info ? formatFileSize(movie.video_info.file_size_bytes) : 'Unknown';
    
    return `
        <div class="movie-card" data-movie-id="${movie.id}">
            <div class="movie-poster">
                <div class="movie-thumbnail">
                    <video preload="metadata" muted>
                        <source src="${movie.video_url}" type="video/mp4">
                    </video>
                    <div class="play-overlay">
                        <span class="play-icon">▶️</span>
                    </div>
                </div>
                <div class="movie-status ${movie.status}">
                    ${movie.status === 'completed' ? '✅' : '⏳'}
                </div>
            </div>
            
            <div class="movie-info">
                <h3 class="movie-title">${movie.title}</h3>
                <div class="movie-meta">
                    <span class="movie-genre">🎬 ${movie.genre}</span>
                    <span class="movie-style">🎨 ${movie.style}</span>
                </div>
                <div class="movie-stats">
                    <span class="stat">
                        <span class="stat-icon">📅</span>
                        ${createdDate}
                    </span>
                    <span class="stat">
                        <span class="stat-icon">⏱️</span>
                        ${duration}
                    </span>
                    <span class="stat">
                        <span class="stat-icon">💾</span>
                        ${fileSize}
                    </span>
                    <span class="stat">
                        <span class="stat-icon">🎬</span>
                        ${movie.num_scenes} scenes
                    </span>
                </div>
                
                <div class="movie-actions">
                    <button class="btn-action btn-view" onclick="viewMovie('${movie.id}')">
                        <span class="btn-icon">👁️</span>
                        View Details
                    </button>
                    <button class="btn-action btn-download" onclick="downloadMovie('${movie.id}')">
                        <span class="btn-icon">📥</span>
                        Download
                    </button>
                    <button class="btn-action btn-delete" onclick="deleteMovie('${movie.id}')">
                        <span class="btn-icon">🗑️</span>
                        Delete
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Setup event listeners
function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', function() {
        filterMovies();
    });
    
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterMovies();
        });
    });
}

// Filter movies based on search and filter
function filterMovies() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;
    
    filteredMovies = movies.filter(movie => {
        const matchesSearch = movie.title.toLowerCase().includes(searchTerm) ||
                            movie.genre.toLowerCase().includes(searchTerm) ||
                            movie.style.toLowerCase().includes(searchTerm);
        
        const matchesFilter = activeFilter === 'all' || 
                            (activeFilter === 'completed' && movie.status === 'completed') ||
                            (activeFilter === 'in-progress' && movie.status !== 'completed');
        
        return matchesSearch && matchesFilter;
    });
    
    displayMovies();
}

// View movie details
async function viewMovie(movieId) {
    try {
        console.log(`👁️ Viewing movie: ${movieId}`);
        const response = await fetch(`/api/movies/${movieId}`);
        const data = await response.json();
        
        if (data.success) {
            showMovieModal(data.movie);
        } else {
            showError('Failed to load movie details: ' + data.error);
        }
    } catch (error) {
        console.error('❌ Error viewing movie:', error);
        showError('Error loading movie details: ' + error.message);
    }
}

// Show movie details modal
function showMovieModal(movie) {
    const modal = document.getElementById('movieModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = movie.title;
    
    const createdDate = new Date(movie.created_at * 1000).toLocaleDateString();
    const duration = movie.video_info ? formatDuration(movie.video_info.duration_seconds) : 'Unknown';
    const fileSize = movie.video_info ? formatFileSize(movie.video_info.file_size_bytes) : 'Unknown';
    
    modalBody.innerHTML = `
        <div class="movie-details">
            <div class="movie-header">
                <div class="movie-poster-large">
                    <video controls preload="metadata">
                        <source src="${movie.video_url}" type="video/mp4">
                    </video>
                </div>
                <div class="movie-info-large">
                    <h3>${movie.title}</h3>
                    <div class="movie-meta">
                        <span class="meta-item">🎬 ${movie.genre}</span>
                        <span class="meta-item">🎨 ${movie.style}</span>
                        <span class="meta-item">📅 ${createdDate}</span>
                    </div>
                    <div class="movie-stats">
                        <div class="stat-item">
                            <span class="stat-label">Duration:</span>
                            <span class="stat-value">${duration}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">File Size:</span>
                            <span class="stat-value">${fileSize}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Scenes:</span>
                            <span class="stat-value">${movie.num_scenes}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Resolution:</span>
                            <span class="stat-value">${movie.video_info?.resolution || 'Unknown'}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            ${movie.description ? `
                <div class="movie-description">
                    <h4>Description</h4>
                    <p>${movie.description}</p>
                </div>
            ` : ''}
            
            ${movie.scenes && movie.scenes.length > 0 ? `
                <div class="movie-scenes">
                    <h4>Scenes</h4>
                    <div class="scenes-list">
                        ${movie.scenes.map((scene, index) => `
                            <div class="scene-item">
                                <div class="scene-number">${index + 1}</div>
                                <div class="scene-content">
                                    <h5>${scene.title || `Scene ${scene.id}`}</h5>
                                    <p>${scene.content.substring(0, 200)}${scene.content.length > 200 ? '...' : ''}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    
    modal.style.display = 'block';
}

// Close modal
function closeModal() {
    const modal = document.getElementById('movieModal');
    modal.style.display = 'none';
}

// Download movie
function downloadMovie(movieId) {
    console.log(`📥 Downloading movie: ${movieId}`);
    const downloadUrl = `/api/movies/${movieId}/download`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Delete movie
async function deleteMovie(movieId) {
    if (!confirm('Are you sure you want to delete this movie? This action cannot be undone.')) {
        return;
    }
    
    try {
        console.log(`🗑️ Deleting movie: ${movieId}`);
        const response = await fetch(`/api/movies/${movieId}/delete`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Movie deleted successfully');
            // Remove from local arrays
            movies = movies.filter(m => m.id !== movieId);
            filteredMovies = filteredMovies.filter(m => m.id !== movieId);
            displayMovies();
            showSuccess('Movie deleted successfully');
        } else {
            showError('Failed to delete movie: ' + data.error);
        }
    } catch (error) {
        console.error('❌ Error deleting movie:', error);
        showError('Error deleting movie: ' + error.message);
    }
}

// Utility functions
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function showError(message) {
    // Simple error display - you can enhance this with a proper notification system
    alert('Error: ' + message);
}

function showSuccess(message) {
    // Simple success display - you can enhance this with a proper notification system
    alert('Success: ' + message);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('movieModal');
    if (event.target === modal) {
        closeModal();
    }
}
