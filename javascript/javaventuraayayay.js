
/* le fonction para el desktop amigo: */ 


document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on desktop
    const isDesktop = window.matchMedia('(min-width: 769px)').matches;

    if (isDesktop) {
        // Create the side title element
        const sideTitle = document.createElement('div');
        sideTitle.classList.add('side-title');
        document.body.appendChild(sideTitle);

        // Create the progress bar
        const progressBar = document.createElement('div');
        progressBar.classList.add('side-progress-bar');
        sideTitle.appendChild(progressBar);

        // Get the main title
        const mainTitle = document.querySelector('h1');
        if (mainTitle) {
            sideTitle.innerHTML += `<h2>${mainTitle.textContent}</h2>`;
        }

        // Throttle function to limit update frequency
        const throttle = (func, limit) => {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        };

        // Update progress and title position
        const updateProgress = throttle(() => {
            const scrollPosition = window.pageYOffset;
            const pageHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercentage = (scrollPosition / pageHeight) * 100;

            progressBar.style.height = `${scrollPercentage}%`;

            // Parallax effect for the title
            sideTitle.style.transform = `translateY(${scrollPosition * 0.1}px)`;
        }, 10); // Throttle to 10ms

        window.addEventListener('scroll', updateProgress);
        window.addEventListener('resize', updateProgress);

        // Initial update
        updateProgress();
    }
});

// Add this to your CSS file or <style> tag
const styles = `
@media (min-width: 769px) {
    .side-title {
        position: fixed;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        writing-mode: vertical-rl;
        text-orientation: mixed;
        font-family: 'Arial', sans-serif;
        font-size: 24px;
        color: #fff;
        background: rgba(0, 0, 0, 0.7);
        padding: 20px 10px;
        border-radius: 10px;
        z-index: 1000;
        transition: transform 0.1s ease-out;
    }

    .side-title h2 {
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-height: 80vh;
    }

    .side-progress-bar {
        position: absolute;
        left: 0;
        bottom: 0;
        width: 4px;
        background: #4CAF50;
        transition: height 0.1s ease-out;
    }
}
`;

const styleSheet = document.createElement("style");
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

/* this function is for mobile */ 
document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('.mobile-header');
    const progressBar = document.querySelector('.progress-bar');
    const showHeaderThreshold = 100; // Pixels scrolled before showing header

    window.addEventListener('scroll', () => {
        const scrollPosition = window.pageYOffset;
        const pageHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercentage = (scrollPosition / pageHeight) * 100;

        progressBar.style.width = `${scrollPercentage}%`;

        if (scrollPosition > showHeaderThreshold) {
            header.style.transform = 'translateY(0)';
        } else {
            header.style.transform = 'translateY(-100%)';
        }
    });
});




        function positionFootnotes() {
            const footnoteRefs = document.querySelectorAll('.footnote-ref');
            const footnotes = document.querySelectorAll('.footnote');
            const footnotesContainer = document.querySelector('.footnotes');
            const containerTop = footnotesContainer.getBoundingClientRect().top;

            let lastBottom = 0;

            footnoteRefs.forEach((ref, index) => {
                const footnote = footnotes[index];
                const refRect = ref.getBoundingClientRect();
                const footnoteHeight = footnote.offsetHeight;

                let top = Math.max(refRect.top - containerTop, lastBottom);

                footnote.style.top = `${top}px`;

                lastBottom = top + footnoteHeight + 10; // 10px gap between footnotes
            });
        }

        // Run on load and resize
        window.addEventListener('load', positionFootnotes);
        window.addEventListener('resize', positionFootnotes);
