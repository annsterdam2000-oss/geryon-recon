// panel/modules/renders/geo.js
import { field, escapeHtml } from "../utils.js";

export function renderGeoResult(r) {
    const parts = [];

    // основные
    const rows = [];
    rows.push(field("Запрос", r.target));
    rows.push(field("Тип ввода", r.input_type === "coords" ? "координаты" : "адрес"));
    if (r.lat != null && r.lon != null) {
        const coords = `${r.lat}, ${r.lon}`;
        const mapLink = `<a href="https://www.openstreetmap.org/?mlat=${r.lat}&mlon=${r.lon}#map=17/${r.lat}/${r.lon}" target="_blank" rel="noopener">${coords}</a>`;
        rows.push(field("Координаты", mapLink));
    }
    if (r.type) rows.push(field("Тип объекта", r.type));
    parts.push(`<table class="kv">${rows.join("")}</table>`);

    // адрес
    const a = r.address || {};
    if (Object.keys(a).length) {
        parts.push(`
            <details open>
                <summary>Адрес</summary>
                <table class="kv">
                    ${field("Страна", a.country ? `${a.country} (${a.country_code || "?"})` : null)}
                    ${field("Регион", a.region)}
                    ${field("Город", a.city)}
                    ${field("Район", a.suburb)}
                    ${field("Улица", a.road)}
                    ${field("Дом", a.house_number)}
                    ${field("Индекс", a.postcode)}
                    ${field("Полный адрес", a.display_name)}
                </table>
            </details>
        `);
    }

    // что рядом
    const n = r.nearby || [];
    if (n.length) {
        const items = n.map(item => {
            if (item.error) return `<div class="warn">${escapeHtml(item.error)}</div>`;
            const dist = item.distance_m != null ? `${item.distance_m} м` : "—";
            const cat = item.subtype ? `${item.category}:${item.subtype}` : (item.category || "");
            return `<tr>
                <td>${escapeHtml(item.name || "")}</td>
                <td>${escapeHtml(cat)}</td>
                <td>${dist}</td>
            </tr>`;
        }).join("");
        parts.push(`
            <details open>
                <summary>Что рядом (100 м) — ${n.length}</summary>
                <table class="kv nearby">
                    <thead><tr><th>Название</th><th>Категория</th><th>Расстояние</th></tr></thead>
                    <tbody>${items}</tbody>
                </table>
            </details>
        `);
    } else {
        parts.push(`<div class="warn">Рядом (100 м) ничего не найдено</div>`);
    }

    return parts.join("");
}