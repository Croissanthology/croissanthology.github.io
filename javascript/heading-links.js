// Converts post headings into anchor links
// Ensures headings without IDs receive generated ones and wraps them in <a href="#..."> links

document.addEventListener('DOMContentLoaded', () => {
  const headings = document.querySelectorAll('.post-content h1, .post-content h2, .post-content h3, .post-content h4, .post-content h5, .post-content h6');
  if (!headings.length) return;

  headings.forEach(h => {
    if (!h.id) {
      h.id = h.textContent.trim().toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
    }

    if (h.querySelector('.heading-link')) return;

    const link = document.createElement('a');
    link.className = 'heading-link';
    link.href = `#${h.id}`;

    while (h.firstChild) {
      link.appendChild(h.firstChild);
    }

    h.appendChild(link);
  });
});
