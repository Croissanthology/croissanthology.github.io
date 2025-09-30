document.addEventListener('DOMContentLoaded', () => {
  const content = document.querySelector('.post-content');
  if (!content) return;

  const headings = content.querySelectorAll('h2, h3, h4, h5, h6');
  if (headings.length === 0) return;

  const firstHeading = headings[0];
  const introNodes = [];
  let node = content.firstChild;
  while (node && node !== firstHeading) {
    const next = node.nextSibling;
    introNodes.push(node);
    node = next;
  }

  const introDiv = document.createElement('div');
  introDiv.className = 'post-intro';
  introNodes.forEach(n => introDiv.appendChild(n));

  const tocList = document.createElement('ol');
  const counters = [];

  headings.forEach(h => {
    const level = parseInt(h.tagName.substring(1));
    if (level < 2) return;
    const depth = level - 2;

    counters[depth] = (counters[depth] || 0) + 1;
    counters.length = depth + 1;
    const number = counters.join('.');

    if (!h.id) {
      h.id = `toc-${number.replace(/\./g, '-')}`;
    }

    const li = document.createElement('li');
    li.style.marginLeft = depth * 16 + 'px';

    const a = document.createElement('a');
    a.className = 'toc-link';
    a.href = '#' + h.id;
    const numSpan = document.createElement('span');
    numSpan.className = 'toc-number';
    numSpan.textContent = number;
    a.appendChild(numSpan);
    a.append(' ' + h.textContent);
    li.appendChild(a);
    tocList.appendChild(li);
  });

  const tocNav = document.createElement('nav');
  tocNav.className = 'post-toc';
  tocNav.appendChild(tocList);

  const wrapper = document.createElement('div');
  wrapper.className = 'toc-and-intro';
  wrapper.appendChild(tocNav);
  wrapper.appendChild(introDiv);

  content.insertBefore(wrapper, firstHeading);
});
