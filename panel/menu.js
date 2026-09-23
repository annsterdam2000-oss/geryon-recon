/* ============================================================
   Geryon Recon — menu.js
   Логика главного экрана:
     - плавные переходы между страницами
     - пасхалка NOSIGNAL (2 мин бездействия → чёрный экран + глаз)
     - кровь из-под сферы после NOSIGNAL (три капли)
   ============================================================ */

(function () {
    'use strict';

    /* ---------- Плавные переходы между страницами ---------- */

    const TRANSITION_MS = 250;

    function isInternalLink(a) {
        if (!a || !a.href) return false;
        if (a.target === '_blank') return false;
        if (a.hasAttribute('download')) return false;
        const url = new URL(a.href, location.href);
        if (url.origin !== location.origin) return false;
        if (url.pathname === location.pathname && url.hash) return false;
        return true;
    }

    document.addEventListener('click', function (e) {
        const a = e.target.closest('a');
        if (!a || !isInternalLink(a)) return;
        e.preventDefault();
        document.body.classList.add('leaving');
        setTimeout(function () {
            location.href = a.href;
        }, TRANSITION_MS);
    });

    /* ---------- Пасхалки ---------- */

    const IDLE_MS     = 2 * 60 * 1000;    // 2 минуты бездействия
    const NOSIGNAL_MS = 5 * 1000;         // 5 секунд чёрного экрана
    const RESET_AFTER = 10 * 60 * 1000;   // повтор не раньше 10 минут

    const overlay = document.getElementById('nosignal-overlay');

    if (!overlay) return;

    let idleTimer   = null;
    let closeTimer  = null;
    let lastShownAt = 0;
    let isActive    = false;

    /* --- Кровь из-под сферы после NOSIGNAL --- */

    function triggerBlood() {
        document.body.classList.add('is-bleeding');
        setTimeout(function () {
            document.body.classList.remove('is-bleeding');
        }, 8000);
    }

    /* --- NOSIGNAL --- */

    function resetIdleTimer() {
        if (isActive) return;
        clearTimeout(idleTimer);
        idleTimer = setTimeout(triggerNosignal, IDLE_MS);
    }

    function triggerNosignal() {
        const now = Date.now();
        if (now - lastShownAt < RESET_AFTER) {
            resetIdleTimer();
            return;
        }

        lastShownAt = now;
        isActive = true;
        overlay.classList.add('is-active');

        closeTimer = setTimeout(function () {
            overlay.classList.remove('is-active');
            isActive = false;
            triggerBlood();
            resetIdleTimer();
        }, NOSIGNAL_MS);
    }

    /* --- Слушаем всё, что означает «пользователь здесь» --- */

    const ACTIVITY_EVENTS = [
        'mousemove', 'mousedown', 'keydown',
        'scroll', 'touchstart', 'wheel', 'click'
    ];

    ACTIVITY_EVENTS.forEach(function (evt) {
        window.addEventListener(evt, resetIdleTimer, { passive: true });
    });

    /* Старт */
    resetIdleTimer();

})();