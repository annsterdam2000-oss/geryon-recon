// panel/modules/bots.js

const botCards = {};

export function renderBots(bots, botsEl, onRefresh) {
    const seen = new Set();
    bots.forEach(b => {
        seen.add(b.bot_id);
        let card = botCards[b.bot_id];
        if (!card) {
            card = document.createElement("div");
            card.className = "bot";
            card.innerHTML = `
                <div class="row">
                    <b class="host"></b>
                    <code class="id"></code>
                    <span class="status"></span>
                    <button class="rm">✕</button>
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
        card.querySelector(".host").textContent = b.hostname;
        card.querySelector(".id").textContent = b.bot_id;
        card.querySelector(".status").textContent = b.status;
        card.querySelector(".info").textContent = `${b.info.os} / ${b.info.user}`;
        card.querySelector(".modules").textContent =
            "модули: " + (b.modules || []).join(", ") +
            (b.current_task ? ` | занят: ${b.current_task}` : " | свободен");
    });
    Object.keys(botCards).forEach(id => {
        if (!seen.has(id)) { botCards[id].remove(); delete botCards[id]; }
    });
}