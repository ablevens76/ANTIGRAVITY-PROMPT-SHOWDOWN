/**
 * ANTIGRAVITY PROMPT SHOWDOWN
 * Interactive Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    initStars();
    initScrollAnimations();
    initParallax();
    initCardInteractions();
});

/**
 * Create animated star background
 */
function initStars() {
    const container = document.getElementById('stars');
    const starCount = 150;

    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        star.className = 'star';

        // Random position
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;

        // Random size
        const size = Math.random() * 2 + 1;
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;

        // Random animation properties
        star.style.setProperty('--duration', `${Math.random() * 3 + 2}s`);
        star.style.setProperty('--opacity', Math.random() * 0.7 + 0.3);
        star.style.animationDelay = `${Math.random() * 3}s`;

        container.appendChild(star);
    }

    // Add shooting stars occasionally
    setInterval(createShootingStar, 4000);
}

/**
 * Create a shooting star effect
 */
function createShootingStar() {
    const container = document.getElementById('stars');
    const shootingStar = document.createElement('div');

    shootingStar.style.cssText = `
        position: absolute;
        width: 100px;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent);
        top: ${Math.random() * 40}%;
        left: ${Math.random() * 60}%;
        transform: rotate(${Math.random() * 30 + 15}deg);
        opacity: 0;
        animation: shootingStar 1s ease-out forwards;
    `;

    container.appendChild(shootingStar);

    setTimeout(() => shootingStar.remove(), 1000);
}

// Add shooting star keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes shootingStar {
        0% {
            opacity: 1;
            transform: translateX(0) translateY(0) rotate(35deg);
        }
        100% {
            opacity: 0;
            transform: translateX(300px) translateY(100px) rotate(35deg);
        }
    }
`;
document.head.appendChild(style);

/**
 * Initialize scroll-based animations using Intersection Observer
 */
function initScrollAnimations() {
    const cards = document.querySelectorAll('.project-card');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                // Add staggered delay based on card index
                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, index * 100);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    cards.forEach(card => observer.observe(card));
}

/**
 * Simple parallax effect on scroll
 */
function initParallax() {
    const hero = document.querySelector('.hero-content');
    const starsContainer = document.getElementById('stars');

    let ticking = false;

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                const scrollY = window.scrollY;

                // Parallax for hero content
                if (hero && scrollY < window.innerHeight) {
                    hero.style.transform = `translateY(${scrollY * 0.3}px)`;
                    hero.style.opacity = 1 - (scrollY / (window.innerHeight * 0.8));
                }

                // Slower parallax for stars
                if (starsContainer) {
                    starsContainer.style.transform = `translateY(${scrollY * 0.1}px)`;
                }

                ticking = false;
            });
            ticking = true;
        }
    });
}

/**
 * Enhanced card interactions with mouse tracking glow
 */
function initCardInteractions() {
    const cards = document.querySelectorAll('.project-card');

    cards.forEach(card => {
        const glow = card.querySelector('.card-glow');

        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Move glow to follow cursor
            if (glow) {
                glow.style.background = `radial-gradient(
                    600px circle at ${x}px ${y}px,
                    rgba(102, 126, 234, 0.15),
                    transparent 40%
                )`;
            }

            // Subtle 3D tilt effect
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 30;
            const rotateY = (centerX - x) / 30;

            card.style.transform = `
                translateY(-8px) 
                perspective(1000px) 
                rotateX(${rotateX}deg) 
                rotateY(${rotateY}deg)
            `;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            if (glow) {
                glow.style.background = '';
            }
        });
    });
}

/**
 * Smooth scroll for anchor links
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

/**
 * Navbar background opacity on scroll
 */
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 100) {
        navbar.style.background = 'rgba(10, 10, 15, 0.95)';
    } else {
        navbar.style.background = 'rgba(10, 10, 15, 0.8)';
    }
});

/**
 * Console Easter Egg
 */
console.log('%c🚀 ANTIGRAVITY PROMPT SHOWDOWN',
    'font-size: 24px; font-weight: bold; color: #764ba2;');
console.log('%c6 AI Models • 6 Projects • 1 Prompt',
    'font-size: 14px; color: #667eea;');
console.log('%cExplore the frontier of AI code generation.',
    'font-size: 12px; color: #888;');
