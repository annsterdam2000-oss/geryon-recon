// panel/panel.js — точка входа
import { refresh, initTaskControls } from "./modules/tasks.js";

initTaskControls();
refresh();
setInterval(refresh, 1000);