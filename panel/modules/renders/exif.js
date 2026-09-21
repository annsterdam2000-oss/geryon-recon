// panel/modules/renders/exif.js
import { field, escapeHtml } from "../utils.js";

export function renderExifResult(r) {
    const parts = [];

    // основные
    const rows = [];
    rows.push(field("Источник", r.source === "url" ? "🌐 URL" : "📁 файл"));
    rows.push(field("Формат", r.format));
    rows.push(field("Размер", r.size_bytes ? `${(r.size_bytes / 1024).toFixed(1)} KB` : null));
    if (r.dimensions) {
        rows.push(field("Разрешение", `${r.dimensions.width} × ${r.dimensions.height}`));
    }
    if (r.has_exif === false) {
        rows.push(field("EXIF", "❌ отсутствует", "warn"));
    } else if (r.has_exif === true) {
        rows.push(field("EXIF", "✅ есть", "good"));
    }
    parts.push(`<table class="kv">${rows.join("")}</table>`);

    // устройство / дата
    const meta = [];
    if (r.datetime) meta.push(field("Дата съёмки", r.datetime));
    if (r.make) meta.push(field("Производитель", r.make));
    if (r.model) meta.push(field("Модель", r.model));
    if (r.software) meta.push(field("Софт", r.software));
    if (r.orientation) meta.push(field("Ориентация", r.orientation));
    if (meta.length) {
        parts.push(`
            <details open>
                <summary>Метаданные</summary>
                <table class="kv">${meta.join("")}</table>
            </details>
        `);
    }

    // GPS
    if (r.has_gps && r.gps) {
        const g = r.gps;
        const mapLink = `<a href="https://www.openstreetmap.org/?mlat=${g.lat}&mlon=${g.lon}#map=17/${g.lat}/${g.lon}" target="_blank" rel="noopener">${g.lat}, ${g.lon}</a>`;
        parts.push(`
            <details open>
                <summary>📍 GPS</summary>
                <table class="kv">
                    ${field("Координаты", mapLink)}
                    ${field("Высота", g.altitude)}
                    ${field("Timestamp", g.timestamp)}
                </table>
            </details>
        `);

        // geo-обогащение
        if (r.geo && r.geo.address) {
            const a = r.geo.address;
            parts.push(`
                <details open>
                    <summary>🏠 Адрес (по GPS)</summary>
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

            const n = r.geo.nearby || [];
            if (n.length) {
                const items = n.map(item => {
                    const dist = item.distance_m != null ? `${item.distance_m} м` : "—";
                    const cat = item.subtype ? `${item.category}:${item.subtype}` : (item.category || "");
                    return `<tr><td>${escapeHtml(item.name || "")}</td><td>${escapeHtml(cat)}</td><td>${dist}</td></tr>`;
                }).join("");
                parts.push(`
                    <details>
                        <summary>Что рядом — ${n.length}</summary>
                        <table class="kv">
                            <thead><tr><th>Название</th><th>Категория</th><th>Расстояние</th></tr></thead>
                            <tbody>${items}</tbody>
                        </table>
                    </details>
                `);
            } else if (r.geo.nearby_error) {
                parts.push(`<div class="warn">Что рядом: ${escapeHtml(r.geo.nearby_error)}</div>`);
            }
        }
    } else if (r.has_exif) {
        parts.push(`<div class="warn">GPS в EXIF отсутствует</div>`);
    }

    // raw EXIF
    const raw = r.raw || {};
    const rawKeys = Object.keys(raw);
    if (rawKeys.length) {
        const rawRows = rawKeys.map(k => {
            const v = raw[k];
            const val = typeof v === "object" ? JSON.stringify(v) : String(v);
            return field(k, val);
        }).join("");
        parts.push(`
            <details>
                <summary>Все EXIF-теги (${rawKeys.length})</summary>
                <table class="kv">${rawRows}</table>
            </details>
        `);
    }

    return parts.join("");
}