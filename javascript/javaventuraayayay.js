document.addEventListener('DOMContentLoaded', () => {
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

    // ===== FEEDBACK SYSTEM =====
    const popup = document.createElement('div');
    popup.className = 'feedback-popup';
    document.body.appendChild(popup);

    document.addEventListener('mouseup', () => {
        const selection = window.getSelection();
        const text = selection.toString().trim();
        
        if (text) {
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            
            // Create a proper mailto link
            popup.innerHTML = `<a href="mailto:croissanthology@gmail.com?subject=Thoughts about ${document.title}&body=${encodeURIComponent(`"${text}"\n\nMy thoughts:\n`)}">💭 Share feedback</a>`;
            
            popup.style.left = `${rect.left + (rect.width / 2)}px`;
            popup.style.top = `${rect.bottom + window.scrollY + 10}px`;
            popup.classList.add('visible');
        } else {
            popup.classList.remove('visible');
        }
    });

    // Hide popup when clicking outside
    document.addEventListener('mousedown', (e) => {
        if (!popup.contains(e.target)) {
            popup.classList.remove('visible');
        }
    });
});
