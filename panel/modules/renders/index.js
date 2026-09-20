// panel/modules/renders/index.js
import { renderEmailResult } from "./email.js";
import { renderEmailRegResult } from "./email_reg.js";
import { renderDomainResult } from "./domain.js";
import { renderUsernameResult } from "./username.js";
import { renderIpResult } from "./ip.js";
import { renderPhoneResult } from "./phone.js";
import { renderPersonResult } from "./person.js";
import { escapeHtml } from "../utils.js";

export function renderResult(type, r, subtasksFull) {
    if (type === "email") return renderEmailResult(r);
    if (type === "email_reg") return renderEmailRegResult(r);
    if (type === "domain") return renderDomainResult(r);
    if (type === "username") return renderUsernameResult(r, subtasksFull);
    if (type === "ip") return renderIpResult(r);
    if (type === "phone") return renderPhoneResult(r);
    if (type === "person") return renderPersonResult(r);
    return `<pre>${escapeHtml(JSON.stringify(r, null, 2))}</pre>`;
}