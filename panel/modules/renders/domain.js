// panel/modules/renders/domain.js
import { field, fmtDate, escapeHtml } from "../utils.js";

export function renderDomainResult(r) {
    const parts = [];

    if (r._timings) {
        const timings = Object.entries(r._timings)
            .map(([k, v]) => `${k}: ${v}с`)
            .join(" | ");
        parts.push(`<div class="timings">⏱ ${escapeHtml(timings)}</div>`);
    }

    const w = r.whois || {};
    parts.push(`
        <details open>
            <summary>WHOIS</summary>
            <table class="kv">
                ${field("Регистратор", w.registrar)}
                ${field("Создан", fmtDate(w.creation_date))}
                ${field("Обновлён", fmtDate(w.updated_date))}
                ${field("Истекает", fmtDate(w.expiration_date))}
                ${field("Организация", w.org)}
                ${field("Страна", w.country)}
                ${field("NS", (w.name_servers || []).join(", "))}
                ${field("Статус", (w.status || []).join(", "))}
                ${field("Emails", (w.emails || []).join(", "))}
            </table>
        </details>
    `);

    const dns = r.dns || {};
    let dnsRows = "";
    for (const [k, v] of Object.entries(dns)) {
        dnsRows += field(k, (v || []).length ? v.join(", ") : "— нет",
                         (v || []).length ? "good" : "bad");
    }
    parts.push(`
        <details open>
            <summary>DNS</summary>
            <table class="kv">${dnsRows}</table>
        </details>
    `);

    const subs = r.subdomains || [];
    const liveSubs = r.subdomains_live || [];
    if (subs.length) {
        const aliveCount = r.subdomains_live_count ?? liveSubs.filter(s => s.alive).length;
        let rows;
        if (liveSubs.length) {
            rows = liveSubs.map(s => {
                const icon = s.alive ? "✅" : "❌";
                const cls = s.alive ? "found" : "notfound";
                const status = s.http_status ? `<code>${s.http_status}</code>` : "";
                const ip = s.ip ? `<code>${escapeHtml(s.ip)}</code>` : "—";
                const redirect = s.redirect
                    ? `<div class="snippet">→ ${escapeHtml(s.redirect)}</div>` : "";
                const err = s.error ? `<span class="warn-text">(${escapeHtml(s.error)})</span>` : "";
                return `
                    <tr class="us-row ${cls}" data-status="${s.alive ? "found" : "notfound"}">
                        <td class="us-site">${icon} ${escapeHtml(s.host)}</td>
                        <td class="us-status">${status} ${err}</td>
                        <td class="us-url">${ip}</td>
                    </tr>
                `;
            }).join("");
        } else {
            rows = subs.map(s => `<code>${escapeHtml(s)}</code>`).join("");
            rows = `<div class="subs">${rows}</div>`;
        }

        const header = liveSubs.length
            ? `Поддомены (${aliveCount} из ${subs.length} живых)`
            : `Поддомены (${r.subdomains_count ?? subs.length})`;

        parts.push(`
            <details open>
                <summary>${header}</summary>
                ${liveSubs.length
                    ? `<div class="username-filter">
                         <label><input type="checkbox" class="df-only-alive" checked> только живые</label>
                       </div>
                       <table class="us-table">
                           <thead><tr><th>Поддомен</th><th>HTTP</th><th>IP</th></tr></thead>
                           <tbody>${rows}</tbody>
                       </table>`
                    : rows}
            </details>
        `);
    }

    const sslInfo = r.ssl || {};
    if (Object.keys(sslInfo).length) {
        const issue = sslInfo.issuer || {};
        const subj = sslInfo.subject || {};
        const daysLeft = _daysUntil(sslInfo.not_after);
        const daysCls = daysLeft === null ? "" : (daysLeft < 14 ? "bad" : daysLeft < 30 ? "warn" : "good");
        parts.push(`
            <details>
                <summary>SSL-сертификат</summary>
                <table class="kv">
                    ${field("Выдан", issue.organizationName || issue.commonName)}
                    ${field("Кому", subj.commonName || subj.organizationName)}
                    ${field("Действует с", fmtDate(sslInfo.not_before))}
                    ${field("Истекает", fmtDate(sslInfo.not_after), daysCls)}
                    ${daysLeft !== null ? field("Осталось дней", daysLeft, daysCls) : ""}
                    ${field("SAN", (sslInfo.san || []).slice(0, 15).join(", ") + ((sslInfo.san_count || 0) > 15 ? ` …(+${sslInfo.san_count - 15})` : ""))}
                    ${sslInfo.error ? field("Ошибка", sslInfo.error, "warn") : ""}
                </table>
            </details>
        `);
    }

    const h = r.http || {};
    parts.push(`
        <details>
            <summary>HTTP</summary>
            <table class="kv">
                ${field("Статус", h.status)}
                ${field("Server", h.server)}
                ${field("X-Powered-By", h.powered_by)}
                ${field("Финальный URL", h.final_url)}
                ${h.error ? field("Ошибка", h.error, "warn") : ""}
            </table>
        </details>
    `);

    return parts.join("");
}

function _daysUntil(iso) {
    if (!iso) return null;
    try {
        const d = new Date(iso);
        const now = new Date();
        return Math.floor((d - now) / (1000 * 60 * 60 * 24));
    } catch {
        return null;
    }
}