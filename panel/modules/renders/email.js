// panel/modules/renders/email.js
import { field } from "../utils.js";

export function renderEmailResult(r) {
    const rows = [];
    rows.push(field("Email", r.target));
    rows.push(field("Логин", r.local));
    rows.push(field("Домен", r.domain));
    rows.push(field("MX", r.mx?.length ? r.mx.join(", ") : "— нет", !r.mx?.length ? "bad" : "good"));
    rows.push(field("A-записи", r.a_records?.length ? r.a_records.join(", ") : "— нет", !r.a_records?.length ? "bad" : "good"));
    if (r.gravatar === true) rows.push(field("Gravatar", "✅ есть", "good"));
    else if (r.gravatar === false) rows.push(field("Gravatar", "❌ нет", "bad"));
    else rows.push(field("Gravatar", "⚠ не удалось проверить", "warn"));
    if (r.gravatar_error) rows.push(field("Ошибка Gravatar", r.gravatar_error, "warn"));
    return `<table class="kv">${rows.join("")}</table>`;
}