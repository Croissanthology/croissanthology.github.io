



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
