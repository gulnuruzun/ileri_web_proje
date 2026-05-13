document.addEventListener('DOMContentLoaded', function() {

    // --- mobil menü ---
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
        // sayfa dışına tıklayınca kapatma
        document.addEventListener('click', function(e) {
            if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
                navLinks.classList.remove('active');
            }
        });
    }

    // --- alert otomatik kapanma ---
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() { alert.remove(); }, 300);
        }, 3000);
    });

    // --- ders arama ---
    const searchInput = document.getElementById('courseSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const cards = document.querySelectorAll('.course-card');
            cards.forEach(function(card) {
                const title = card.querySelector('.course-title').textContent.toLowerCase();
                const code = card.querySelector('.course-code').textContent.toLowerCase();
                card.style.display = (title.includes(query) || code.includes(query)) ? '' : 'none';
            });
        });
    }

    // --- yazdır butonu ---
    const printBtn = document.getElementById('printBtn');
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            window.print();
        });
    }

});