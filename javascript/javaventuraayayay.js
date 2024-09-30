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
      
        }
    }

    window.addEventListener('scroll', updateProgressBar);
    window.addEventListener('resize', updateProgressBar);

    // Initial update
    updateProgressBar();
});

