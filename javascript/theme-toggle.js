document.addEventListener('DOMContentLoaded', () => {
    const darkLink = document.getElementById('toggle-dark');
    const systemLink = document.getElementById('toggle-system');

    function applyTheme(theme) {
        if (theme === 'system') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
    }

    function setTheme(theme) {
        localStorage.setItem('theme', theme);
        applyTheme(theme);
    }

    const saved = localStorage.getItem('theme') || 'system';
    applyTheme(saved);

    if (darkLink) {
        darkLink.addEventListener('click', (e) => {
            e.preventDefault();
            const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            setTheme(current);
        });
    }

    if (systemLink) {
        systemLink.addEventListener('click', (e) => {
            e.preventDefault();
            setTheme('system');
        });
    }
});
