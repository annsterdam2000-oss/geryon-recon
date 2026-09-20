// panel/modules/renders/ip.js
import { field, fmtDate, escapeHtml } from "../utils.js";

export function renderIpResult(r) {
    const parts = [];

    const g = r.geo || {};
    if (Object.keys(g).length) {
        const coords = (g.lat && g.lon) ? `${g.lat}, ${g.lon}` : null;
        const mapLink = (g.lat && g.lon)
            ? `<a href="https://www.openstreetmap.org/?mlat=${g.lat}&mlon=${g.lon}#map=12/${g.lat}/${g.lon}" target="_blank" rel="noopener">${coords}</a>`
            : coords;
        parts.push(`
            <details open>
                <summary>Гео</summary>
                <table class="kv">
                    ${field("Страна", g.country ? `${g.country} (${g.country_code || "?"})` : null)}
                    ${field("Регион", g.region)}
                    ${field("Город", g.city)}
                    ${field("Индекс", g.zip)}
                    ${field("Координаты", mapLink)}
                    ${field("Часовой пояс", g.timezone)}
                </table>
            </details>
        `);
    } else if (r.geo_error) {
        parts.push(`<div class="warn">Гео: ${escapeHtml(r.geo_error)}</div>`);
    }

    const n = r.network || {};
    if (Object.keys(n).length) {
        const flags = [];
        if (n.mobile) flags.push("📱 мобильный");
        if (n.proxy) flags.push("🎭 прокси/VPN");
        if (n.hosting) flags.push("🖥 хостинг/датацентр");
        parts.push(`
            <details open>
                <summary>Провайдер</summary>
                <table class="kv">
                    ${field("ISP", n.isp)}
                    ${field("Организация", n.org)}
                    ${field("ASN", n.as)}
                    ${field("ASN name", n.asname)}
                    ${field("Признаки", flags.length ? flags.join(", ") : "—")}
                </table>
            </details>
        `);
    }

    const ptr = r.ptr || [];
    parts.push(`
        <details>
            <summary>Reverse DNS (PTR)</summary>
            ${ptr.length
                ? `<table class="kv">${ptr.map(p => field("PTR", p)).join("")}</table>`
                : `<div class="warn">PTR-записи не найдены</div>`}
        </details>
    `);

    const w = r.whois || {};
    if (Object.keys(w).length) {
        parts.push(`
            <details>
                <summary>Whois (RIR)</summary>
                <table class="kv">
                    ${field("Network", w.netname)}
                    ${field("CIDR", w.cidr)}
                    ${field("Диапазон", w.start_address && w.end_address ? `${w.start_address} — ${w.end_address}` : null)}
                    ${field("Страна", w.country)}
                    ${field("ASN", w.asn)}
                    ${field("ASN описание", w.asn_description)}
                    ${field("ASN страна", w.asn_country)}
                    ${field("Зарегистрирован", fmtDate(w.registered))}
                </table>
            </details>
        `);
    } else if (r.whois_error) {
        parts.push(`<div class="warn">Whois: ${escapeHtml(r.whois_error)}</div>`);
    }

    return parts.join("");
}