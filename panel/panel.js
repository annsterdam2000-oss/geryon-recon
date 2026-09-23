// panel/panel.js — точка входа
import { refresh, initTaskControls } from "./modules/tasks.js";

// --- подпись в консоли ---
console.log(
    "%c☄ Geryon Recon %c— Invoker is casting.",
    "color: #c8aa6e; font-weight: bold; font-size: 14px;",
    "color: #8b93a1; font-size: 12px;"
);
console.log(
    "%cQuas. Wex. Exort. Server. Agent. Panel. Three spheres, three bodies, one mind.",
    "color: #5a6270; font-style: italic; font-size: 11px;"
);

// --- init ---
initTaskControls();
refresh();
setInterval(refresh, 3000);