



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


document.addEventListener('DOMContentLoaded', () => {
    const footnoteRefs = document.querySelectorAll('.footnote-ref');
    const overlay = document.createElement('div');
    overlay.className = 'footnote-overlay';
    document.body.appendChild(overlay);

    footnoteRefs.forEach(ref => {
        ref.addEventListener('click', (e) => {
            e.preventDefault();
            const footnoteId = ref.getAttribute('data-footnote');
            const footnote = document.getElementById(`footnote-${footnoteId}`);
            
            if (window.innerWidth <= 768) {
                footnote.classList.add('active');
                overlay.classList.add('active');
            }
            
            ref.classList.add('animate');
            setTimeout(() => ref.classList.remove('animate'), 500);
        });
    });

    overlay.addEventListener('click', () => {
        document.querySelectorAll('.footnote').forEach(footnote => footnote.classList.remove('active'));
        overlay.classList.remove('active');
    });
});
