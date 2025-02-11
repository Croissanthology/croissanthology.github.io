document.addEventListener('DOMContentLoaded', () => {
    // Add side title styles
    const styles = `
        @media (min-width: 769px) {
            .side-title {
                position: fixed;
                left: 20px;
                top: 50%;
                transform: translateY(-50%);
                writing-mode: vertical-rl;
                text-orientation: mixed;
                font-family: 'Arial', sans-serif;
                font-size: 24px;
                color: #fff;
                background: rgba(0, 0, 0, 0.7);
                padding: 20px 10px;
                border-radius: 10px;
                z-index: 1000;
                transition: transform 0.1s ease-out;
            }

            .side-title h2 {
                margin: 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-height: 80vh;
            }

            .side-progress-bar {
                position: absolute;
                left: 0;
                bottom: 0;
                width: 4px;
                background: #4CAF50;
                transition: height 0.1s ease-out;
            }
        }
    `;

    const styleSheet = document.createElement("style");
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
}); 