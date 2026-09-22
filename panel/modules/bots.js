// panel/modules/bots.js

const botCards = {};

// --- группы модулей по цвету ---
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

// --- SVG сфера с сеткой (одна на всех) ---
const SPHERE_SVG = `
<svg class="mod-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" aria-hidden="true">
    <circle cx="8" cy="8" r="6.2"/>
    <ellipse cx="8" cy="8" rx="6.2" ry="2.6"/>
    <ellipse cx="8" cy="8" rx="2.6" ry="6.2"/>
    <line x1="1.8" y1="8" x2="14.2" y2="8"/>
</svg>`;

export function renderBots(bots, botsEl, onRefresh) {
    if (!bots.length) {
        botsEl.innerHTML = `
            <div class="empty">
                <div class="empty-icon">${SPHERE_SVG}</div>
                <div class="empty-title">Агентов нет</div>
                <div class="empty-sub">Запусти <code>python agent.py --count 3</code> в папке <code>agent/</code></div>
            </div>`;
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

        // --- модули: сфера + цвет по группе ---
        const modEl = card.querySelector(".modules");
        const mods = b.modules || [];
        let html = mods.map(m => {
            const group = MODULE_GROUPS[m] || "tech";
            return `<span class="mod mod-${group}">${SPHERE_SVG}${m}</span>`;
        }).join("");
        if (b.current_task) {
            html += `<span class="mod mod-busy">${SPHERE_SVG}busy: ${b.current_task}</span>`;
        } else {
            html += `<span class="mod mod-idle">idle</span>`;
        }
        modEl.innerHTML = html;
    });

    Object.keys(botCards).forEach(id => {
        if (!seen.has(id)) { botCards[id].remove(); delete botCards[id]; }
    });
}