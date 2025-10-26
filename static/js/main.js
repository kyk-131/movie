// Landing page animations and interactions
document.addEventListener('DOMContentLoaded', function() {
    // Add floating animation to geometric shapes
    const shapes = document.querySelectorAll('.cube, .sphere, .pyramid');
    
    shapes.forEach(shape => {
        shape.style.animation = `float ${Math.random() * 3 + 2}s ease-in-out infinite`;
    });
});

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes float {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(10deg); }
    }
    
    .cube, .sphere, .pyramid {
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
`;
document.head.appendChild(style);
