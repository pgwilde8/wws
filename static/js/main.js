// Main JavaScript file

document.addEventListener('DOMContentLoaded', () => {
    console.log('[nav] script loaded');
    
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (!hamburgerBtn || !mobileMenu) {
        console.warn('[nav] hamburger or mobile menu not found');
        return;
    }
    
    hamburgerBtn.addEventListener('click', () => {
        const isOpen = mobileMenu.classList.toggle('open');
        hamburgerBtn.classList.toggle('active', isOpen);
        document.body.classList.toggle('no-scroll', isOpen);
        console.log('[nav] menu is now', isOpen ? 'open' : 'closed');
    });
    
    // Close menu when clicking on a link
    const mobileLinks = mobileMenu.querySelectorAll('a');
    mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
            mobileMenu.classList.remove('open');
            hamburgerBtn.classList.remove('active');
            document.body.classList.remove('no-scroll');
        });
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Stripe Connect button logic
    const stripeBtn = document.getElementById('stripeOnboardBtn');
    if (stripeBtn) {
        stripeBtn.onclick = async function() {
            const btn = this;
            btn.disabled = true;
            btn.textContent = 'Connecting...';
            document.getElementById('stripeOnboardMsg').textContent = '';
            const stripeWin = window.open('', '_blank', 'noopener');
            try {
                const user_id = window.currentUserId || 'demo';
                const resp = await fetch('/pay/stripe/onboard-link', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id })
                });
                if (!resp.ok) throw new Error('Could not create onboarding link');
                const data = await resp.json();
                if (data.url) {
                    stripeWin.location = data.url;
                    window.location.href = '/onboarding-in-progress';
                } else {
                    stripeWin.close();
                    throw new Error('No onboarding URL received');
                }
            } catch (err) {
                if (stripeWin) stripeWin.close();
                document.getElementById('stripeOnboardMsg').textContent = err.message || 'Error connecting to Stripe.';
                btn.disabled = false;
                btn.textContent = 'Connect Stripe Account';
            }
        };
    }
});
