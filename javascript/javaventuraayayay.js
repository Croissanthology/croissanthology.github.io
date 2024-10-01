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

  headers.forEach((header, index) => {
    // Give the header an id if it doesn't have one
    if (!header.id) {
      header.id = `toc-header-${index}`;
    }

    const listItem = document.createElement('li');
    const link = document.createElement('a');
    link.textContent = header.textContent;
    link.href = `#${header.id}`;
    
    // Set class based on header level
    listItem.className = `toc-item toc-${header.tagName.toLowerCase()}`;

    link.addEventListener('click', (e) => {
      e.preventDefault();
      header.scrollIntoView({ behavior: 'smooth' });
    });

    listItem.appendChild(link);
    tocList.appendChild(listItem);
  });

  toc.appendChild(tocList);
  tocContainer.appendChild(toc);
});
