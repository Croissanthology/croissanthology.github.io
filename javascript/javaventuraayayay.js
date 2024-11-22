document.addEventListener('DOMContentLoaded', () => {
    // ===== FEEDBACK SYSTEM =====
    const popup = document.createElement('div');
    popup.className = 'feedback-popup';
    document.body.appendChild(popup);

    document.addEventListener('mouseup', (e) => {
        const selection = window.getSelection();
        const text = selection.toString().trim();
        
        if (text) {
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            
            const subject = encodeURIComponent(`Thoughts about ${document.title}`);
            const body = encodeURIComponent(`"${text}"\n\nMy thoughts:\n`);
            
            popup.innerHTML = `<a 
                href="mailto:croissanthology@gmail.com?subject=${subject}&body=${body}"
                class="feedback-link"
            >💭 Share feedback</a>`;
            
            popup.style.left = `${rect.left + (rect.width / 2)}px`;
            popup.style.top = `${rect.bottom + window.scrollY + 10}px`;
            popup.classList.add('visible');
        } else {
            popup.classList.remove('visible');
        }
    });

    document.addEventListener('mousedown', (e) => {
        if (!popup.contains(e.target)) {
            popup.classList.remove('visible');
        }
    });

    // ===== HEADER & PROGRESS BAR =====
    const header = document.querySelector('.mobile-header');
    const progressBar = document.querySelector('.progress-bar');
    const showHeaderThreshold = 100;

    function updateProgressBar() {
        const scrollPercentage = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        progressBar.style.width = `${scrollPercentage}%`;
        header.style.transform = `translateY(${window.scrollY > showHeaderThreshold ? '0' : '-100%'})`;
    }

    window.addEventListener('scroll', updateProgressBar);
    updateProgressBar();

    // ===== HEADING LINKS =====
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    headings.forEach(heading => {
        heading.innerHTML = `<span class="heading-container">${heading.innerHTML}</span>`;
        heading.addEventListener('click', () => {
            const pageUrl = window.location.href.split('#')[0];
            const headingLink = `${pageUrl}#${heading.id}`;
            navigator.clipboard.writeText(headingLink).then(() => {
                console.log('Link copied to clipboard:', headingLink);
            }).catch(err => {
                console.error('Failed to copy link:', err);
            });
        });
    });

    // ===== UNDER CONSTRUCTION LINKS =====
    const links = document.querySelectorAll('a[href$="under-construction.html"]');
    links.forEach(link => {
        if (!link.querySelector('.soon-prefix')) {
            const prefix = document.createElement('span');
            prefix.className = 'soon-prefix';
            prefix.textContent = '[SOON] ';
            link.insertBefore(prefix, link.firstChild);
        }
    });

    // ===== TABLE OF CONTENTS =====
    const tocContainer = document.querySelector('.auto-toc');
    if (tocContainer && document.querySelectorAll('h2, h3, h4, h5, h6').length > 0) {
        const toc = document.createElement('nav');
        toc.className = 'toc-nav';
        // Your TOC code here
    }
});
