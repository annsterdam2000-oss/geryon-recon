// panel/modules/renders/email_reg.js
import { escapeHtml } from "../utils.js";

export function renderEmailRegResult(r) {
    const parts = [];

    const reg = r.registered || [];
    const notReg = r.not_registered || [];
    const unknown = r.unknown || [];
    const rate = r.rate_limited || [];
    const total = r.total_checked ?? (reg.length + notReg.length + unknown.length + rate.length);

    parts.push(`
        <div class="username-summary">
            <b>${escapeHtml(r.target || "")}</b> —
            зарегистрирован на <span class="good-text">${reg.length}</span> из ${total}
        </div>
    `);

    if (reg.length) {
        parts.push(`
            <details open>
                <summary>✅ Зарегистрирован (${reg.length})</summary>
                <div class="subs">${reg.map(s => `<code>${escapeHtml(s)}</code>`).join("")}</div>
            </details>
        `);
    }

    if (unknown.length) {
        parts.push(`
            <details>
                <summary>⚠ Неизвестно (${unknown.length})</summary>
                <div class="subs">${unknown.map(s => `<code>${escapeHtml(s)}</code>`).join("")}</div>
            </details>
        `);
    }

    if (rate.length) {
        parts.push(`
            <details>
                <summary>🚫 Rate-limit (${rate.length})</summary>
                <div class="subs">${rate.map(s => `<code>${escapeHtml(s)}</code>`).join("")}</div>
            </details>
        `);
    }

    if (notReg.length) {
        parts.push(`
            <details>
                <summary>❌ Не зарегистрирован (${notReg.length})</summary>
                <div class="subs">${notReg.map(s => `<code>${escapeHtml(s)}</code>`).join("")}</div>
            </details>
        `);
    }

    return parts.join("");
}