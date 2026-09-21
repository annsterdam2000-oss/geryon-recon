// panel/modules/renders/telegram.js
import { field, escapeHtml } from "../utils.js";

export function renderTelegramResult(r) {
    const rows = [];

    rows.push(field("Запрос", r.target));
    rows.push(field("Username", r.username ? `@${r.username}` : null));
    rows.push(field("Ссылка", r.url
        ? `<a href="${escapeHtml(r.url)}" target="_blank" rel="noopener">${escapeHtml(r.url)}</a>`
        : null));

    // существование
    if (r.exists === true) {
        rows.push(field("Существует", "✅ да", "good"));
    } else if (r.exists === false) {
        rows.push(field("Существует", "❌ нет", "bad"));
    }

    // тип
    const kindLabels = {
        user: "👤 пользователь",
        channel: "📢 канал",
        group: "👥 группа/чат",
        bot: "🤖 бот",
    };
    if (r.kind) {
        rows.push(field("Тип", kindLabels[r.kind] || r.kind));
    }

    // имя, описание, аватар
    if (r.title) rows.push(field("Имя", r.title));
    if (r.description) rows.push(field("Описание", r.description));
    if (r.image) {
        rows.push(field("Аватар",
            `<img src="${escapeHtml(r.image)}" alt="avatar" style="max-width:64px;border-radius:50%">`));
    }

    // HTTP-статус (для отладки)
    if (r.http_status) rows.push(field("HTTP", r.http_status));
    if (r.error) rows.push(field("Ошибка", escapeHtml(r.error), "warn"));

    return `<table class="kv">${rows.join("")}</table>`;
}