const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..');
const postsDir = path.join(repoRoot, '_posts');
const logPath = path.join(repoRoot, 'log.json');
const countsPath = path.join(repoRoot, 'word_counts.json');

function wordCount(text){
  return text.trim().split(/\s+/).filter(Boolean).length;
}

const previousCounts = fs.existsSync(countsPath) ? JSON.parse(fs.readFileSync(countsPath, 'utf8')) : {};
const log = fs.existsSync(logPath) ? JSON.parse(fs.readFileSync(logPath, 'utf8')) : {};

const currentCounts = {};
fs.readdirSync(postsDir).filter(f => f.endsWith('.md')).forEach(file => {
  const content = fs.readFileSync(path.join(postsDir, file), 'utf8');
  currentCounts[file] = wordCount(content);
});

const changes = [];
for(const [file, count] of Object.entries(currentCounts)){
  const prev = previousCounts[file] || 0;
  const delta = count - prev;
  if(delta !== 0){
    const datePart = file.slice(0,10);
    const [y,m,d] = datePart.split('-');
    const slug = file.slice(11,-3);
    const url = `/${y}/${m}/${d}/${slug}.html`;
    changes.push({ title: slug, url, delta });
  }
}

if(changes.length > 0){
  const date = new Date();
  date.setDate(date.getDate()-1);
  const key = date.toISOString().split('T')[0];
  log[key] = changes;
  fs.writeFileSync(logPath, JSON.stringify(log, null, 2));
  fs.writeFileSync(countsPath, JSON.stringify(currentCounts, null, 2));
}
