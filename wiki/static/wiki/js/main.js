document.addEventListener('DOMContentLoaded', function() {
    const nav = document.querySelector('.main-nav');
    const featuredImage = document.querySelector('.featured-image-container');
    const contextMenu = document.querySelector('.context_menu');
    const contentHolder = document.querySelector('.content_holder');
    // Hamburger menu elements
    const hamburger = document.querySelector('.hamburger-menu');
    const slidingMenu = document.querySelector('.sliding-menu');
    const menuOverlay = document.querySelector('.menu-overlay');

    // Debug logging
    console.log('Menu elements:', {
        hamburger: hamburger,
        slidingMenu: slidingMenu,
        menuOverlay: menuOverlay
    });

    // Simple menu toggle function
    function toggleMenu(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        const isCurrentlyOpen = slidingMenu.classList.contains('open');
        console.log('Current menu state before toggle:', isCurrentlyOpen);

        if (!isCurrentlyOpen) {
            // Opening the menu
            slidingMenu.style.display = 'block';
            menuOverlay.style.display = 'block';
            // Force a reflow
            slidingMenu.offsetHeight;
            menuOverlay.offsetHeight;
            
            slidingMenu.classList.add('open');
            menuOverlay.classList.add('open');
            document.body.style.overflow = 'hidden';
            console.log('Menu opened');
        } else {
            // Closing the menu
            slidingMenu.classList.remove('open');
            menuOverlay.classList.remove('open');
            document.body.style.overflow = '';
            
            // Wait for transition to complete before hiding
            setTimeout(() => {
                if (!slidingMenu.classList.contains('open')) {
                    slidingMenu.style.display = 'none';
                    menuOverlay.style.display = 'none';
                }
            }, 300);
            console.log('Menu closed');
        }
    }

    // Add event listeners for menu
    if (hamburger) {
        console.log('Adding click listener to hamburger');
        // Remove any existing listeners
        const newHamburger = hamburger.cloneNode(true);
        hamburger.parentNode.replaceChild(newHamburger, hamburger);
        
        // Add new click listener
        newHamburger.addEventListener('click', toggleMenu, { passive: false });
        newHamburger.addEventListener('touchend', function(e) {
            e.preventDefault();
            toggleMenu(e);
        }, { passive: false });
    }

    if (menuOverlay) {
        menuOverlay.addEventListener('click', toggleMenu);
        menuOverlay.addEventListener('touchend', toggleMenu);
    }

    // Context menu position update
    function updateContextMenuPosition() {
        if (!contextMenu || !contentHolder) return;
        
        const scrollPosition = window.scrollY;
        const navHeight = nav.offsetHeight;
        const contentTop = contentHolder.offsetTop;

        if (scrollPosition + navHeight >= contentTop) {
            contextMenu.classList.add('sticky');
            contextMenu.style.top = `${navHeight}px`;
        } else {
            contextMenu.classList.remove('sticky');
            contextMenu.style.top = `${contentTop}px`;
        }
    }

    // Add scroll listener
    window.addEventListener('scroll', updateContextMenuPosition);

    // Handle window resize
    window.addEventListener('resize', function() {
        if (contentHolder) {
            contextMenuInitialOffset = contentHolder.offsetTop;
            updateContextMenuPosition();
        }
    });

    // Initial context menu position
    if (contextMenu && contentHolder) {
        contextMenu.style.top = `${contentHolder.offsetTop}px`;
    }

    // New function to toggle featured image visibility
    function toggleFeaturedImage() {
        featuredImage.classList.toggle('hidden');
        contentHolder.classList.toggle('no-featured-image');
        window.dispatchEvent(new CustomEvent('contentLayoutChange'));
    }

    // Function to toggle login state
    function toggleLoginState() {
        const navComponent = document.getElementById('main-nav');
        if (navComponent.hasAttribute('logged-in')) {
            navComponent.removeAttribute('logged-in');
        } else {
            navComponent.setAttribute('logged-in', '');
        }
    }

    document.addEventListener('click', function(event) {
        if (event.target.closest('.login_btn') || event.target.closest('.dropdown-toggle')) {
            toggleLoginState();
        }
    });
});
