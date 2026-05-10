const footerHTML = `
    <div class="container footer-content">
        <div class="footer-left">
            <div class="logo">
                <span class="logo-icon">✋</span>
                MP_Gesture_Lib
            </div>
            <p>Open-source gesture recognition for Python.</p>
            <p class="copyright" style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.5rem;">&copy; Debabrata Saha. All rights reserved.</p>
        </div>
        <div class="footer-right">
            <a href="https://github.com/debabratasaha-dev/mp-gesture-lib-package" class="footer-link">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
                GitHub Repository
            </a>
            <a href="#" class="footer-link">PyPI Package</a>
        </div>
    </div>
`;

document.addEventListener('DOMContentLoaded', () => {

    // Inject Footer
    const footerEls = document.querySelectorAll('footer');
    footerEls.forEach(el => {
        el.innerHTML = footerHTML;
    });

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
