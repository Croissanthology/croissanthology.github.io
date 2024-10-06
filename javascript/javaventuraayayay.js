document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('.mobile-header');
    const progressBar = document.querySelector('.progress-bar');
    const showHeaderThreshold = 100;

    function updateProgressBar() {
        const scrollPercentage = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        progressBar.style.width = `${scrollPercentage}%`;
        header.style.transform = `translateY(${window.scrollY > showHeaderThreshold ? '0' : '-100%'})`;
    }

    window.addEventListener('scroll', updateProgressBar);
    updateProgressBar(); // Initial call
});

/* Table of contents */

document.addEventListener('DOMContentLoaded', () => {
  const tocContainer = document.querySelector('.auto-toc');
  if (!tocContainer) return; // Bail if there's no ToC container

  const headers = document.querySelectorAll('h2, h3, h4, h5, h6');
  if (headers.length === 0) return; // Bail if there are no headers

  const toc = document.createElement('nav');
  toc.className = 'toc-nav';
  const tocList = document.createElement('ul');

  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');
    const headers = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    console.log(`Found ${headers.length} headers`);
    
    headers.forEach((header, index) => {
        if (!header.id) {
            header.id = `header-${index}`;
        }
        console.log(`Processing header: ${header.textContent} with id: ${header.id}`);
        
        header.addEventListener('click', (event) => {
            event.preventDefault();
            const pageUrl = window.location.href.split('#')[0];
            const headerLink = `${pageUrl}#${header.id}`;
            console.log(`Attempting to copy link: ${headerLink}`);
            
            if (navigator.clipboard) {
                navigator.clipboard.writeText(headerLink)
                    .then(() => {
                        console.log('Link successfully copied to clipboard');
                        alert('Link copied to clipboard!');
                    })
                    .catch(err => {
                        console.error('Failed to copy link: ', err);
                        alert('Failed to copy link. See console for details.');
                    });
            } else {
                console.warn('Clipboard API not available');
                // Fallback method
                const textArea = document.createElement('textarea');
                textArea.value = headerLink;
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    console.log('Link copied using fallback method');
                    alert('Link copied to clipboard!');
                } catch (err) {
                    console.error('Fallback method failed: ', err);
                    alert('Failed to copy link. See console for details.');
                }
                document.body.removeChild(textArea);
            }
        });
    });
});
