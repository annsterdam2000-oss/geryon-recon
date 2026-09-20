// panel/modules/utils.js

export function field(name, value, cls = "") {
    const v = (value === null || value === undefined || value === "")
        ? "—" : value;
    return `<tr class="${cls}"><td class="k">${escapeHtml(name)}</td><td class="v">${escapeHtml(String(v))}</td></tr>`;
}

export function fmtDate(s) {
    if (!s) return null;
    try { return new Date(s).toLocaleString("ru-RU"); }
    catch { return s; }
}

export function escapeHtml(s) {
    return String(s)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
}

export function simpleHash(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) {
        h = ((h << 5) - h + str.charCodeAt(i)) | 0;
    }
    return h;
}