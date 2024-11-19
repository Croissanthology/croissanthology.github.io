 const popup = document.createElement('div');
        popup.className = 'feedback-popup';

        document.addEventListener('mouseup', () => {
            const selection = window.getSelection();
            const text = selection.toString().trim();
            
            if (text) {
                const range = selection.getRangeAt(0);
                const rect = range.getBoundingClientRect();
                
                // Just set the innerHTML to a proper mailto link!
                popup.innerHTML = `<a href="mailto:croissanthology@gmail.com?subject=Thoughts&body=${encodeURIComponent(`"${text}"\n\nMy thoughts:\n`)}">💭 Share feedback</a>`;
                
                popup.style.left = `${rect.left + (rect.width / 2)}px`;
                popup.style.top = `${rect.bottom + window.scrollY + 10}px`;
                popup.classList.add('visible');
            } else {
                popup.classList.remove('visible');
            }
        });

        // Still need this to hide popup when clicking outside
        document.addEventListener('mousedown', (e) => {
            if (!popup.contains(e.target)) {
                popup.classList.remove('visible');
            }
        });



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
    
    const button = document.createElement('button');
    button.className = 'feedback-button';
    button.innerHTML = '💭 Share feedback';
    
    popup.appendChild(button);
    document.body.appendChild(popup);

    document.addEventListener('mouseup', () => {
        const selection = window.getSelection();
        const text = selection.toString().trim();
        
        if (text) {
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            popup.style.left = `${rect.left + (rect.width / 2)}px`;
            popup.style.top = `${rect.bottom + window.scrollY + 10}px`;
            popup.classList.add('visible');
        } else {
            popup.classList.remove('visible');
        }
    });

    button.addEventListener('click', () => {
        const text = window.getSelection().toString().trim();
        const postTitle = document.title || 'Croissanthology Post';
        window.location.href = `mailto:croissanthology@gmail.com?subject=Thoughts about ${postTitle}&body=${encodeURIComponent(`"${text}"\n\nMy thoughts:\n`)}`;
        popup.classList.remove('visible');
    });

    document.addEventListener('mousedown', (e) => {
        if (!popup.contains(e.target)) {
            popup.classList.remove('visible');
        }
    });
});
