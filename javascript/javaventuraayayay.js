document.addEventListener('DOMContentLoaded', () => {
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



