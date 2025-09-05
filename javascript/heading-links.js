// Adds link-copying functionality to post headings
// When a heading is clicked, its URL is copied to the clipboard

document.addEventListener('DOMContentLoaded', () => {
  const headings = document.querySelectorAll('.post-content h1, .post-content h2, .post-content h3, .post-content h4, .post-content h5, .post-content h6');
  if (!headings.length) return;

  headings.forEach(h => {
    if (!h.id) {
      h.id = h.textContent.trim().toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
    }
    h.addEventListener('click', () => {
      const url = `${window.location.origin}${window.location.pathname}#${h.id}`;
      navigator.clipboard.writeText(url).catch(err => console.error('Copy failed', err));
    });
  });
});
