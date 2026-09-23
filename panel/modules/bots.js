// panel/modules/bots.js

const botCards = {};

const MODULE_GROUPS = {
    "domain":    "net",
    "ip":        "net",
    "phone":     "net",
    "email":     "mail",
    "email_reg": "mail",
    "username":  "id",
    "person":    "id",
    "telegram":  "id",
    "geo":       "meta",
    "exif":      "meta",
    "http_check": "tech",
};

// ============================================================
// ☄ Дота-лор для модулей — тултипы на пилюлях
// ============================================================

const MODULE_LORE = {
    "email":     "Invoker: три сферы — один адрес",
    "email_reg": "Silencer: тихая проверка регистраций",
    "domain":    "Exort: каркас мира — WHOIS, DNS, SSL",
    "username":  "Meepo: 35 копий — одна цель",
    "ip":        "Arc Warden: я и мой цифровой клон",
    "phone":     "Tinker: перехват сигнала",
    "person":    "Chen: собирает под рукой",
    "telegram":  "Wex: молния связи",
    "geo":       "Mars: арена координат, 100 метров",
    "exif":      "Rubick: что украл — то моё",
    "http_check":"Bounty Hunter: ищет по следу",
};

const SPHERE_SVG = `
<svg class="mod-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" aria-hidden="true">
    <circle cx="8" cy="8" r="6.2"/>
    <ellipse cx="8" cy="8" rx="6.2" ry="2.6"/>
    <ellipse cx="8" cy="8" rx="2.6" ry="6.2"/>
    <line x1="1.8" y1="8" x2="14.2" y2="8"/>
</svg>`;

const SPHERE_BIG_SVG = `
<svg class="empty-sphere" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" aria-hidden="true">
    <circle cx="16" cy="16" r="12.4"/>
    <ellipse cx="16" cy="16" rx="12.4" ry="5.2"/>
    <ellipse cx="16" cy="16" rx="5.2" ry="12.4"/>
    <line x1="3.6" y1="16" x2="28.4" y2="16"/>
</svg>`;

const BOLT_SVG = `
<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M9 1.5 L3.5 9 H7.5 L6.5 14.5 L13 6.5 H8.5 Z"/>
</svg>`;

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

export function renderBots(bots, botsEl, onRefresh) {
    if (!bots.length) {
        botsEl.innerHTML = `
            <div class="empty">
                <div class="empty-icon">${SPHERE_BIG_SVG}</div>
                <div class="empty-title">Агентов нет</div>
                <div class="empty-sub">Запусти их, чтобы начать работу</div>
                <button class="empty-btn" id="launch-agents-btn">
                    ${BOLT_SVG}
                    Запустить агентов
                </button>
            </div>`;
        const btn = botsEl.querySelector("#launch-agents-btn");
        if (btn) btn.onclick = showLaunchModal;
        Object.keys(botCards).forEach(id => { delete botCards[id]; });
        return;
    }

    const emptyEl = botsEl.querySelector(".empty");
    if (emptyEl) emptyEl.remove();

    const seen = new Set();
    bots.forEach(b => {
        seen.add(b.bot_id);
        let card = botCards[b.bot_id];
        if (!card) {
            card = document.createElement("div");
            card.className = "bot";
            card.innerHTML = `
                <div class="bot-head">
                    <b class="host"></b>
                    <span class="status"></span>
                    <button class="rm" title="Удалить агента">✕</button>
                </div>
                <div class="info"></div>
                <div class="modules"></div>
            `;
            card.querySelector(".rm").onclick = () =>
                fetch(`/remove/bot/${b.bot_id}`, {method: "POST"}).then(onRefresh);
            botsEl.appendChild(card);
            botCards[b.bot_id] = card;
        }
        card.className = "bot " + b.status;

        const displayName = b.agent_name || b.hostname || b.bot_id;
        const hostEl = card.querySelector(".host");
        hostEl.textContent = displayName;
        hostEl.title = `bot_id: ${b.bot_id}` +
            (b.hostname ? ` · host: ${b.hostname}` : "");

        const statusEl = card.querySelector(".status");
        statusEl.innerHTML = `<span class="sdot"></span>${b.status}`;

        card.querySelector(".info").textContent = `${b.info.os} · ${b.info.user}`;

        const modEl = card.querySelector(".modules");
        const mods = b.modules || [];
        let html = mods.map(m => {
            const group = MODULE_GROUPS[m] || "tech";
            const lore  = MODULE_LORE[m];
            const tip   = lore ? ` data-tooltip="${escapeHtml(lore)}"` : "";
            return `<span class="mod mod-${group}"${tip}>${SPHERE_SVG}${m}</span>`;
        }).join("");
        if (b.current_task) {
            html += `<span class="mod mod-busy" data-tooltip="Выполняет задачу">${SPHERE_SVG}busy: ${escapeHtml(b.current_task)}</span>`;
        } else {
            html += `<span class="mod mod-idle" data-tooltip="Готов к работе">idle</span>`;
        }
        modEl.innerHTML = html;
    });

    Object.keys(botCards).forEach(id => {
        if (!seen.has(id)) { botCards[id].remove(); delete botCards[id]; }
    });
}


// --- модалка "Запустить агентов" ---
function showLaunchModal() {
    let overlay = document.getElementById("launch-modal");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "launch-modal";
        overlay.className = "modal-overlay";
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-head">
                    <span class="modal-title">Запустить агентов</span>
                    <button class="modal-close" title="Закрыть">✕</button>
                </div>
                <div class="modal-body">
                    <p class="modal-hint">Открой новый терминал и выполни:</p>
                    <div class="modal-code">
                        <code id="launch-cmd">cd C:\\projects\\geryon-recon\\agent
python agent.py --count 3</code>
                        <button class="modal-copy" id="launch-copy">Копировать</button>
                    </div>
                    <p class="modal-note">Проверь, что сервер запущен. Агенты подключатся автоматически.</p>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        overlay.querySelector(".modal-close").onclick = () =>
            overlay.classList.remove("open");
        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.classList.remove("open");
        };

        overlay.querySelector("#launch-copy").onclick = () => {
            const text = overlay.querySelector("#launch-cmd").textContent;
            navigator.clipboard.writeText(text).then(() => {
                const btn = overlay.querySelector("#launch-copy");
                const old = btn.textContent;
                btn.textContent = "Скопировано";
                setTimeout(() => { btn.textContent = old; }, 1500);
            });
        };
    }
    overlay.classList.add("open");
}