



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
