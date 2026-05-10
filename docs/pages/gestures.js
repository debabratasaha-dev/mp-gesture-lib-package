const gestureData = [
    {
        id: "plus",
        name: "Plus (+)",
        type: "Rule-based",
        badgeClass: "rule-badge",
        image: "../Gesture_pictures/plus.png",
        tags: ["add", "addition", "sum", "plus", "+"]
    },
    {
        id: "minus",
        name: "Minus (-)",
        type: "ML Model",
        badgeClass: "ml-badge",
        image: "../Gesture_pictures/minus.png",
        tags: ["subtract", "subtraction", "minus", "-"]
    },
    {
        id: "multiply",
        name: "Multiply (*)",
        type: "Rule-based",
        badgeClass: "rule-badge",
        image: "../Gesture_pictures/multiply.png",
        tags: ["multiply", "multiplication", "times", "cross", "*"]
    },
    {
        id: "divide",
        name: "Divide (/)",
        type: "ML Model",
        badgeClass: "ml-badge",
        image: "../Gesture_pictures/divide.png",
        tags: ["divide", "division", "slash", "/"]
    },
    {
        id: "equal",
        name: "Equal (=)",
        type: "ML Model",
        badgeClass: "ml-badge",
        image: "../Gesture_pictures/equal.png",
        tags: ["equal", "equals", "result", "="]
    },
    {
        id: "clear",
        name: "Clear (C)",
        type: "ML Model",
        badgeClass: "ml-badge",
        image: "../Gesture_pictures/clear.png",
        tags: ["clear", "reset", "cancel", "c"]
    },
    {
        id: "zero",
        name: "Zero (0)",
        type: "ML Model",
        badgeClass: "ml-badge",
        image: "../Gesture_pictures/0.png",
        tags: ["zero", "0", "none"]
    },
    {
        id: "numbers",
        name: "Numbers 1-10",
        type: "Finger Count",
        badgeClass: "rule-badge",
        image: null,
        icon: "🔢",
        tags: ["number", "numbers", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "count", "finger"]
    }
];

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('gesture-search');
    const resultsContainer = document.getElementById('gesture-results');
    const noResultsMsg = document.getElementById('no-results');

    // Function to render gesture cards
    function renderGestures(gestures) {
        resultsContainer.innerHTML = '';
        
        if (gestures.length === 0) {
            resultsContainer.style.display = 'none';
            noResultsMsg.classList.remove('hidden');
            return;
        }

        resultsContainer.style.display = 'grid';
        noResultsMsg.classList.add('hidden');

        gestures.forEach((gesture, index) => {
            const card = document.createElement('div');
            card.className = `gesture-card glass-panel ${!gesture.image ? 'special-card' : ''}`;
            card.style.opacity = "0";
            card.style.transform = "translateY(20px)";
            
            // Animation for newly rendered items
            setTimeout(() => {
                card.style.transition = `opacity 0.4s ease, transform 0.4s ease`;
                card.style.opacity = "1";
                card.style.transform = "translateY(0)";
            }, index * 50);

            let mediaHTML = '';
            if (gesture.image) {
                mediaHTML = `
                    <div class="gesture-image-container">
                        <img src="${gesture.image}" alt="${gesture.name}" class="gesture-img" loading="lazy">
                    </div>
                `;
            } else {
                mediaHTML = `
                    <div class="gesture-icon-placeholder">${gesture.icon}</div>
                `;
            }

            card.innerHTML = `
                ${mediaHTML}
                <div class="gesture-info">
                    <h3>${gesture.name}</h3>
                    <span class="badge ${gesture.badgeClass}">${gesture.type}</span>
                    ${gesture.id === 'numbers' ? '<p class="tiny-desc">Detects extended fingers with direction-awareness.</p>' : ''}
                </div>
            `;
            
            resultsContainer.appendChild(card);
        });
    }

    // Initial render
    renderGestures(gestureData);

    // Search functionality
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        
        if (query === '') {
            renderGestures(gestureData);
            return;
        }

        const filtered = gestureData.filter(gesture => {
            // Check name
            if (gesture.name.toLowerCase().includes(query)) return true;
            // Check tags
            return gesture.tags.some(tag => tag.includes(query));
        });

        renderGestures(filtered);
    });
});
