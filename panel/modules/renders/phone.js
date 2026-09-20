// panel/modules/renders/phone.js
import { field } from "../utils.js";

export function renderPhoneResult(r) {
    const parts = [];

    const rows = [];
    rows.push(field("Номер", r.target));
    if (r._assumed_region) {
        rows.push(field("Регион по умолчанию", r._assumed_region, "warn"));
    }

    rows.push(field("Страна (код)", r.country_code ? `+${r.country_code}` : null));
    rows.push(field("Регион (ISO)", r.region_code));

    if (r.is_valid === true) {
        rows.push(field("Валидность", "✅ валидный", "good"));
    } else if (r.is_valid === false) {
        rows.push(field("Валидность", "❌ невалидный", "bad"));
    }

    if (r.is_possible !== undefined) {
        rows.push(field("Возможность", r.is_possible ? "да" : "нет"));
    }

    if (r.region || r.region_en) {
        const reg = r.region || r.region_en;
        const regEn = (r.region_en && r.region_en !== reg) ? ` (${r.region_en})` : "";
        rows.push(field("Гео", `${reg}${regEn}`));
    }

    if (r.carrier) {
        rows.push(field("Оператор", r.carrier));
    }

    if (r.number_type) {
        const cls = r.number_type === "мобильный" ? "good" : "";
        rows.push(field("Тип линии", r.number_type, cls));
    }

    if (r.timezones && r.timezones.length) {
        rows.push(field("Часовые пояса", r.timezones.join(", ")));
    }

    parts.push(`
        <details open>
            <summary>Информация о номере</summary>
            <table class="kv">${rows.join("")}</table>
        </details>
    `);

    const f = r.formats || {};
    if (Object.keys(f).length) {
        parts.push(`
            <details>
                <summary>Форматы</summary>
                <table class="kv">
                    ${field("E.164", f.e164)}
                    ${field("Международный", f.international)}
                    ${field("Национальный", f.national)}
                    ${field("RFC3966", f.rfc3966)}
                </table>
            </details>
        `);
    }

    return parts.join("");
}