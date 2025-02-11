document.addEventListener('DOMContentLoaded', () => {
    // ===== HEADER & PROGRESS BAR =====
    const header = document.querySelector('.mobile-header');
    const progressBar = document.querySelector('.progress-bar');
    const showHeaderThreshold = 100;

    function updateProgressBar() {
        const scrollPercentage = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        progressBar.style.width = `${scrollPercentage}%`;
        header.style.transform = `translateY(${window.scrollY > showHeaderThreshold ? '0' : '-100%'})`;
    }

    window.addEventListener('scroll', updateProgressBar);
    updateProgressBar();

    // ===== HEADING LINKS =====
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    headings.forEach(heading => {
        heading.innerHTML = `<span class="heading-container">${heading.innerHTML}</span>`;
        heading.addEventListener('click', () => {
            const pageUrl = window.location.href.split('#')[0];
            const headingLink = `${pageUrl}#${heading.id}`;
            navigator.clipboard.writeText(headingLink).then(() => {
                console.log('Link copied to clipboard:', headingLink);
            }).catch(err => {
                console.error('Failed to copy link:', err);
            });
        });
    });

    // ===== UNDER CONSTRUCTION LINKS =====
    const links = document.querySelectorAll('a[href$="under-construction.html"]');
    links.forEach(link => {
        if (!link.querySelector('.soon-prefix')) {
            const prefix = document.createElement('span');
            prefix.className = 'soon-prefix';
            prefix.textContent = '[SOON] ';
            link.insertBefore(prefix, link.firstChild);
        }
    });

    // ===== TABLE OF CONTENTS =====
    const tocContainer = document.querySelector('.auto-toc');
    if (tocContainer && document.querySelectorAll('h2, h3, h4, h5, h6').length > 0) {
        const toc = document.createElement('nav');
        toc.className = 'toc-nav';
        // Your TOC code here
    }
});

class Sidenotes {
    constructor() {
        this.config = {
            minWidth: '1761px',
            spacing: 60,
            padding: 13,
            contentSelector: '.content-wrapper',
            selectors: {
                potentialOverlap: [
                    '.width-full img',
                    '.width-full video',
                    '.width-full table',
                    '.marginnote'
                ],
                constrainWithin: [
                    '.margin-notes-block'
                ]
            }
        };
        
        this.state = {
            sidenotes: [],
            citations: [],
            columns: {
                left: null,
                right: null
            },
            storage: null,
            updateQueued: false
        };

        this.init();
    }

    init() {
        this.setupMediaQueries();
        this.constructSidenotes();
        
        // Bind scroll event for position updates
        window.addEventListener('scroll', () => this.updatePositions());
        
        // Bind resize event
        window.addEventListener('resize', () => {
            if (!this.state.updateQueued) {
                window.requestAnimationFrame(() => {
                    this.updatePositions();
                    this.state.updateQueued = false;
                });
                this.state.updateQueued = true;
            }
        });
    }

    setupMediaQueries() {
        this.mediaQuery = window.matchMedia(`(min-width: ${this.config.minWidth})`);
        this.mediaQuery.addEventListener('change', () => this.handleViewportChange());
    }

    constructSidenotes() {
        const content = document.querySelector(this.config.contentSelector);
        if (!content) return;

        // Clear existing
        this.cleanup();

        // Create columns
        this.state.columns.left = this.createColumn('left');
        this.state.columns.right = this.createColumn('right');
        this.state.storage = this.createHiddenStorage();

        content.append(
            this.state.columns.left, 
            this.state.columns.right,
            this.state.storage
        );

        // Process citations
        this.state.citations = Array.from(document.querySelectorAll('a.footnote-ref'));
        if (this.state.citations.length === 0) return;

        // Create sidenotes
        this.state.sidenotes = this.state.citations.map(citation => 
            this.createSidenote(citation)
        );

        // Initial positioning
        this.updatePositions();
    }

    createColumn(side) {
        const column = document.createElement('div');
        column.id = `sidenote-column-${side}`;
        column.className = 'footnotes';
        column.style.visibility = 'hidden';
        return column;
    }

    createHiddenStorage() {
        const storage = document.createElement('div');
        storage.id = 'hidden-sidenote-storage';
        storage.className = 'footnotes';
        storage.style.display = 'none';
        return storage;
    }

    createSidenote(citation) {
        const noteNumber = this.getNoteNumber(citation.hash);
        const sidenote = document.createElement('div');
        sidenote.className = 'sidenote';
        sidenote.id = `sn${noteNumber}`;

        // Create wrappers
        const outerWrapper = document.createElement('div');
        outerWrapper.className = 'sidenote-outer-wrapper';
        const innerWrapper = document.createElement('div');
        innerWrapper.className = 'sidenote-inner-wrapper';

        // Get content
        const referencedFootnote = document.querySelector(`#fn${noteNumber}`);
        const content = referencedFootnote ? 
            referencedFootnote.cloneNode(true) : 
            this.createPlaceholderContent(noteNumber);

        // Assemble
        innerWrapper.appendChild(content);
        outerWrapper.appendChild(innerWrapper);
        sidenote.appendChild(outerWrapper);

        // Add self-link
        const selfLink = document.createElement('a');
        selfLink.className = 'sidenote-self-link';
        selfLink.href = `#sn${noteNumber}`;
        selfLink.textContent = noteNumber;
        sidenote.appendChild(selfLink);

        this.bindSidenoteEvents(sidenote, citation);
        return sidenote;
    }

    bindSidenoteEvents(sidenote, citation) {
        // Hover highlighting
        sidenote.addEventListener('mouseenter', () => {
            citation.classList.add('highlighted');
            this.slideSidenoteIntoView(sidenote, false);
        });
        
        sidenote.addEventListener('mouseleave', () => {
            citation.classList.remove('highlighted');
            this.putSidenoteBack(sidenote);
        });

        // Citation hover
        citation.addEventListener('mouseenter', () => {
            this.slideSidenoteIntoView(sidenote, true);
        });
    }

    updatePositions() {
        if (!this.mediaQuery.matches) return;
        if (this.state.updateQueued) return;

        this.state.updateQueued = true;
        requestAnimationFrame(() => {
            this.state.updateQueued = false;
            this.calculatePositions();
        });
    }

    calculatePositions() {
        // Hide existing
        this.state.sidenotes.forEach(sidenote => {
            if (sidenote.classList.contains('hidden')) {
                this.state.storage.appendChild(sidenote);
                return;
            }
            
            // Determine column
            const noteNumber = this.getNoteNumber(sidenote.id);
            const column = noteNumber % 2 ? this.state.columns.left : this.state.columns.right;
            
            // Position calculation
            const citation = this.getCitation(noteNumber);
            const citationRect = citation.getBoundingClientRect();
            const columnRect = column.getBoundingClientRect();
            
            // Set position
            const top = Math.max(0, citationRect.top - columnRect.top);
            sidenote.style.top = `${top}px`;
            
            // Add to column
            column.appendChild(sidenote);
        });

        // Show columns
        this.state.columns.left.style.visibility = '';
        this.state.columns.right.style.visibility = '';
    }

    // Utility methods
    getNoteNumber(hash) {
        return hash.replace(/^[#]*(fn|sn)/, '');
    }

    getCitation(number) {
        return document.querySelector(`#fnref${number}`);
    }

    cleanup() {
        Object.values(this.state.columns).forEach(column => column?.remove());
        this.state.storage?.remove();
        this.state = {
            sidenotes: [],
            citations: [],
            columns: { left: null, right: null },
            storage: null,
            updateQueued: false
        };
    }

    // Event handlers
    handleViewportChange() {
        if (this.mediaQuery.matches) {
            this.constructSidenotes();
        } else {
            this.cleanup();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.sidenotes = new Sidenotes();
});

document.addEventListener('DOMContentLoaded', function() {
    const footnotes = document.querySelectorAll('.footnotes li');
    const sidenotes = document.querySelectorAll('.sidenote');
    
    sidenotes.forEach((sidenote, index) => {
        if (footnotes[index]) {
            const content = footnotes[index].innerHTML;
            // Remove the backlink
            const cleanContent = content.replace(/<a class="reversefootnote".*?<\/a>/, '');
            sidenote.setAttribute('data-footnote-content', cleanContent);
        }
    });

