// panel/modules/renders/person.js
import { escapeHtml } from "../utils.js";

export function renderPersonResult(r) {
    const parts = [];

    const mentions = r.mentions || [];
    const variants = r.variants || [];

    parts.push(`
        <div class="username-summary">
            <b>${escapeHtml(r.target || "")}</b> —
            найдено упоминаний: <span class="good-text">${mentions.length}</span>
        </div>
    `);

    if (variants.length) {
        parts.push(`
            <details>
                <summary>Варианты ников (транслит)</summary>
                <div class="subs">${variants.map(v => `<code>${escapeHtml(v)}</code>`).join("")}</div>
            </details>
        `);
    }

    if (r._timings) {
        const timings = Object.entries(r._timings)
            .map(([k, v]) => `${k}: ${v}с`)
            .join(" | ");
        parts.push(`<div class="timings">⏱ ${escapeHtml(timings)}</div>`);
    }

    if (mentions.length) {
        const rows = mentions.map(m => `
            <tr>
                <td class="us-site"><b>${escapeHtml(m.source)}</b></td>
                <td class="us-url">
                    <a href="${escapeHtml(m.url)}" target="_blank" rel="noopener">
                        ${escapeHtml(m.title || m.url)}
                    </a>
                    ${m.snippet ? `<div class="snippet">${escapeHtml(m.snippet)}</div>` : ""}
                </td>
            </tr>
        `).join("");

        parts.push(`
            <details open>
                <summary>Упоминания (${mentions.length})</summary>
                <table class="us-table">
                    <thead><tr><th>Источник</th><th>Ссылка</th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </details>
        `);
    } else {
        parts.push(`<div class="warn">Упоминаний не найдено</div>`);
    }

    // ошибки источников
    const sources = r.sources || {};
    const errors = Object.entries(sources).filter(([k]) => k.endsWith("_error"));
    if (errors.length) {
        parts.push(`
            <details>
                <summary>Ошибки источников (${errors.length})</summary>
                <table class="kv">
                    ${errors.map(([k, v]) => `<tr class="warn"><td class="k">${escapeHtml(k)}</td><td class="v">${escapeHtml(v)}</td></tr>`).join("")}
                </table>
            </details>
        `);
    }

    return parts.join("");
}