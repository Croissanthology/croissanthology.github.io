document.addEventListener('DOMContentLoaded', () => {
  fetch('/log.json')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById('log-container');
      const dates = Object.keys(data).sort().reverse();
      dates.forEach(date => {
        const section = document.createElement('section');
        const heading = document.createElement('h2');
        heading.textContent = date;
        section.appendChild(heading);
        const table = document.createElement('table');
        data[date].forEach(entry => {
          const tr = document.createElement('tr');
          const tdLink = document.createElement('td');
          const link = document.createElement('a');
          link.href = entry.url;
          link.textContent = entry.title;
          tdLink.appendChild(link);
          const tdDelta = document.createElement('td');
          tdDelta.textContent = (entry.delta > 0 ? '+' : '') + entry.delta;
          tdDelta.style.color = entry.delta >= 0 ? '#4A9C6D' : '#C04747';
          tr.appendChild(tdLink);
          tr.appendChild(tdDelta);
          table.appendChild(tr);
        });
        section.appendChild(table);
        container.appendChild(section);
      });
    })
    .catch(err => {
      console.error('Failed to load log', err);
    });
});
