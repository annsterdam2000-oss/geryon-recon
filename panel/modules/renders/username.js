// panel/modules/renders/username.js
import { escapeHtml } from "../utils.js";

export function renderUsernameResult(r, subtasksFull) {
    const parts = [];
    const target = r.target || "";
    const found = r.found_count ?? 0;
    const unknown = r.unknown_count ?? 0;
    const total = r.total ?? (r.results || []).length;

    parts.push(`
        <div class="username-summary">
            <b>${escapeHtml(target)}</b> —
            найдено на <span class="good-text">${found}</span> из ${total},
            неизвестно: <span class="warn-text">${unknown}</span>
        </div>
    `);

    parts.push(`
        <div class="username-filter">
            <label><input type="checkbox" class="uf-only-found"> только найденные</label>
            <label><input type="checkbox" class="uf-hide-unknown" checked> скрыть неизвестные</label>
        </div>
    `);

    let items = r.results || [];
    if (subtasksFull && subtasksFull.length) {
        items = subtasksFull.map(s => {
            const res = s.result || {};
            return {
                site: s.site,
                url: res.url || "",
                status: s.status === "done" ? (res.status || "unknown")
                       : s.status === "failed" ? "unknown"
                       : s.status,
                http_code: res.http_code,
                error: s.error || res.error,
            };
        });
    }

    const rows = items.map(item => {
        const cls = item.status === "found" ? "found"
                  : item.status === "not_found" ? "notfound"
                  : item.status === "pending" ? "pending-row"
                  : item.status === "running" ? "running-row"
                  : "unknown";
        const icon = item.status === "found" ? "✅"
                   : item.status === "not_found" ? "❌"
                   : item.status === "pending" ? "⏳"
                   : item.status === "running" ? "🔄"
                   : "⚠";
        const link = item.url
            ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.url)}</a>`
            : "";
        const err = item.error ? `<span class="warn-text">(${escapeHtml(item.error)})</span>` : "";
        return `
            <tr class="us-row ${cls}" data-status="${item.status}">
                <td class="us-site">${icon} ${escapeHtml(item.site || "")}</td>
                <td class="us-status">${item.status}${item.http_code ? ` <code>${item.http_code}</code>` : ""} ${err}</td>
                <td class="us-url">${link}</td>
            </tr>
        `;
    }).join("");

    parts.push(`
        <details open>
            <summary>Сайты (${items.length})</summary>
            <table class="us-table">
                <thead><tr><th>Сайт</th><th>Статус</th><th>Ссылка</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </details>
    `);

    return parts.join("");
}

export function attachUsernameFilters(root) {
    const table = root.querySelector(".us-table");
    if (!table) return;
    const onlyFound = root.querySelector(".uf-only-found");
    const hideUnknown = root.querySelector(".uf-hide-unknown");
    const dfOnlyAlive = root.querySelector(".df-only-alive");

    const apply = () => {
        root.querySelectorAll(".us-row").forEach(row => {
            const status = row.dataset.status;
            let visible = true;
            if (onlyFound?.checked && status !== "found") visible = false;
            if (hideUnknown?.checked && status === "unknown") visible = false;
            if (dfOnlyAlive?.checked && status !== "found") visible = false;
            row.style.display = visible ? "" : "none";
        });
    };

    onlyFound?.addEventListener("change", apply);
    hideUnknown?.addEventListener("change", apply);
    dfOnlyAlive?.addEventListener("change", apply);
    apply();
}