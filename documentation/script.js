document.addEventListener('DOMContentLoaded', () => {
    
    // Copy Install Command functionality
    const copyBtn = document.getElementById('copy-install');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText('pip install mp-gesture-lib').then(() => {
                // Show copied state
                const originalHTML = copyBtn.innerHTML;
                copyBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#27c93f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                }, 2000);
            });
        });
    }

    // Tabs functionality
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            // Add active class to clicked
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // Simple scroll animation for cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Apply animation initial state to elements
    const animateElements = document.querySelectorAll('.feature-card, .gesture-card, .api-card, .tabs-container');
    animateElements.forEach((el, index) => {
        el.style.opacity = "0";
        el.style.transform = "translateY(20px)";
        el.style.transition = `opacity 0.6s ease, transform 0.6s ease`;
        el.style.transitionDelay = `${(index % 3) * 0.1}s`; // Stagger effect based on grid column (roughly)
        observer.observe(el);
    });
    
    // Smooth scroll for nav links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});
