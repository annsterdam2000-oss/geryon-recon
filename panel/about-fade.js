// panel/about-fade.js
// Плавный переход из about в меню

const FADE_MS = 280;

const backLink = document.querySelector("a.about-back");
if (backLink) {
    backLink.addEventListener("click", (e) => {
        e.preventDefault();
        document.body.classList.add("leaving");
        setTimeout(() => {
            window.location.href = backLink.getAttribute("href") || "/";
        }, FADE_MS);
    });
}