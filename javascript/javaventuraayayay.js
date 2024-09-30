document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('.mobile-header');
    const progressBar = document.querySelector('.progress-bar');
    const headerTitle = document.querySelector('.mobile-header-title');
    const showHeaderThreshold = 100;
    const isMobile = () => window.innerWidth < 768;

    // Set the header title
    headerTitle.textContent = document.title;

    function updateProgressBar() {
        const scrollPosition = window.pageYOffset;
        const pageHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercentage = (scrollPosition / pageHeight) * 100;

        progressBar.style.width = `${scrollPercentage}%`;

        if (isMobile()) {
            header.style.transform = scrollPosition > showHeaderThreshold ? 'translateY(0)' : 'translateY(-100%)';
        } else {
            header.style.position = 'fixed';
            header.style.top = '10px';
            header.style.left = '10px';
            header.style.width = 'calc(100% - 20px)';
            header.style.transform = 'translateY(0)';
            header.style.opacity = scrollPosition > showHeaderThreshold ? '1' : '0';
            header.style.transition = 'opacity 0.3s ease-in-out';
        }
    }

    window.addEventListener('scroll', updateProgressBar);
    window.addEventListener('resize', updateProgressBar);

    // Initial update
    updateProgressBar();
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
