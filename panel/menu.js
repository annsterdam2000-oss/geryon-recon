// panel/menu.js
// Плавный переход по клику на ссылки-переходы

const FADE_MS = 280;

function fadeNavigate(url) {
    document.body.classList.add("leaving");
    setTimeout(() => {
        window.location.href = url;
    }, FADE_MS);
}

document.querySelectorAll("a.menu-btn").forEach(link => {
    link.addEventListener("click", (e) => {
        const href = link.getAttribute("href");
        if (!href) return;

        // внешние ссылки (GitHub и т.п.) — открываем как обычно
        if (link.target === "_blank" || href.startsWith("http")) return;

        // внутренние — через fade
        e.preventDefault();
        fadeNavigate(href);
    });
});