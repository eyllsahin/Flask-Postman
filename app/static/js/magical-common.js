// Magical Common JavaScript for Fairy Animations

document.addEventListener("DOMContentLoaded", function() {
    // Create fairy lights
    createFairies(20);
    
    // Add magical sparkle to form inputs
    addSparkleEffects();
});

// Function to create fairy lights
function createFairies(count) {
    const fairyContainer = document.querySelector('.fairy-container');
    if (!fairyContainer) return;
    
    for (let i = 0; i < count; i++) {
        const fairy = document.createElement('div');
        fairy.className = 'fairy';
        
        // Randomize starting position
        fairy.style.left = `${Math.random() * 100}%`;
        fairy.style.top = `${Math.random() * 100}%`;
        
        // Randomize animation timing
        fairy.style.animationDelay = `${Math.random() * 10}s`;
        fairy.style.animationDuration = `${10 + Math.random() * 20}s`;
        
        fairyContainer.appendChild(fairy);
    }
}

// Function to add sparkle effects to inputs and buttons
function addSparkleEffects() {
    // Add magical classes to inputs and buttons for sparkle effects
    const inputs = document.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        input.classList.add('magical-input');
    });
    
    const buttons = document.querySelectorAll('button, .submit-btn, .login-button');
    buttons.forEach(button => {
        button.classList.add('magical-btn');
    });
}

// Optional: Add some subtle movement when moving the mouse
document.addEventListener('mousemove', function(e) {
    const fairies = document.querySelectorAll('.fairy');
    const mouseX = e.clientX / window.innerWidth;
    const mouseY = e.clientY / window.innerHeight;
    
    fairies.forEach((fairy, index) => {
        if (index % 3 === 0) { // Only affect every third fairy for performance
            const offsetX = (mouseX - 0.5) * 20;
            const offsetY = (mouseY - 0.5) * 20;
            fairy.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
        }
    });
});
