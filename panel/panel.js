// panel/panel.js — точка входа

// 1. СНАЧАЛА проверяем авторизацию
let token = localStorage.getItem("geryon_api_key");
if (!token) {
    token = prompt("Введите API-ключ для доступа к панели:");
    if (token) {
        localStorage.setItem("geryon_api_key", token);
    } else {
        document.body.innerHTML = "<h1 style='color:#ff4444; text-align:center; margin-top: 20%; font-family: sans-serif;'>Доступ запрещён.<br>Обновите страницу и введите ключ.</h1>";
        throw new Error("Unauthorized");
    }
}

// 2. Ставим перехватчик ДО того, как загрузятся модули
const originalFetch = window.fetch;
window.fetch = function(resource, config) {
    config = config || {};
    config.headers = config.headers || {};
    
    if (config.headers instanceof Headers) {
        config.headers.append("X-API-Key", token);
    } else {
        config.headers["X-API-Key"] = token;
    }
    
    return originalFetch(resource, config);
};

// 3. Импортируем модули (они уже будут использовать перехваченный fetch)
import { refresh, initTaskControls } from "./modules/tasks.js";

// --- подпись в консоли ---
console.log(
    "%c☄ Geryon Recon %c— Invoker is casting.",
    "color: #c8aa6e; font-weight: bold; font-size: 14px;",
    "color: #8b93a1; font-size: 12px;"
);
console.log(
    "%cQuas. Wex. Exort. Server. Agent. Panel. Three spheres, three bodies, one mind.",
    "color: #5a6270; font-style: italic; font-size: 11px;"
);

// --- init ---
initTaskControls();
refresh();
setInterval(refresh, 3000);