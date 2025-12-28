// Exit intent popup functionality

(function() {
    'use strict';
    
    let exitIntentShown = false;
    const popup = document.getElementById('exit-popup');
    const closeBtn = document.querySelector('.exit-popup-close');
    
    if (!popup) return;
    
    // Show popup
    function showPopup() {
        if (exitIntentShown) return;
        exitIntentShown = true;
        popup.style.display = 'flex';
        popup.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Track popup shown (you can add analytics here)
        console.log('Exit intent popup shown');
    }
    
    // Hide popup
    function hidePopup() {
        popup.style.display = 'none';
        popup.classList.remove('show');
        document.body.style.overflow = '';
    }
    
    // Close button handler
    if (closeBtn) {
        closeBtn.addEventListener('click', hidePopup);
    }
    
    // Close on outside click
    popup.addEventListener('click', function(e) {
        if (e.target === popup) {
            hidePopup();
        }
    });
    
    // Detect exit intent (mouse leaving viewport)
    document.addEventListener('mouseout', function(e) {
        if (!e.toElement && !e.relatedTarget && e.clientY < 10) {
            showPopup();
        }
    });
    
    // Fallback: Show popup after user has been on page for 30 seconds
    setTimeout(function() {
        if (!exitIntentShown) {
            // Only show if user is still on page
            document.addEventListener('mouseleave', function(e) {
                if (e.clientY <= 0 && !exitIntentShown) {
                    showPopup();
                }
            });
        }
    }, 30000);
    
    // Store in localStorage that popup was shown (to avoid showing too often)
    if (localStorage.getItem('exitPopupShown')) {
        exitIntentShown = true;
    } else {
        // Mark as shown in localStorage when popup is displayed
        const originalShow = showPopup;
        showPopup = function() {
            originalShow();
            localStorage.setItem('exitPopupShown', 'true');
            // Reset after 24 hours
            setTimeout(function() {
                localStorage.removeItem('exitPopupShown');
            }, 24 * 60 * 60 * 1000);
        };
    }
})();

