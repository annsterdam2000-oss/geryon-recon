// panel/modules/tasks.js
import { renderBots } from "./bots.js";
import { renderResult } from "./renders/index.js";
import { captureDetailsState, restoreDetailsState } from "./details.js";
import { escapeHtml, simpleHash } from "./utils.js";
import { attachUsernameFilters } from "./renders/username.js";

const taskCards = {};
const taskResultHash = {};
const taskLastPct = {};      // ← запоминаем последний % для плавного прогресса
const taskProgressEls = {};  // ← ссылки на .pbar и .pfill, чтобы не пересоздавать

let currentFilter = "all";   // ← фильтр задач

const botsEl   = document.getElementById("bots");
const tasksEl  = document.getElementById("tasks");
const typeSel  = document.getElementById("task-type");
const targetInput = document.getElementById("task-target");
const addBtn   = document.getElementById("task-add");

const botsCountEl  = document.getElementById("bots-count");
const tasksCountEl = document.getElementById("tasks-count");
const filterEl     = document.getElementById("task-filter");

const SPHERE_SVG = `
<svg class="empty-sphere" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" aria-hidden="true">
    <circle cx="16" cy="16" r="12.4"/>
    <ellipse cx="16" cy="16" rx="12.4" ry="5.2"/>
    <ellipse cx="16" cy="16" rx="5.2" ry="12.4"/>
    <line x1="3.6" y1="16" x2="28.4" y2="16"/>
</svg>`;


export async function refresh() {
    try {
        const [bots, tasks] = await Promise.all([
            fetch("/bots").then(r => r.json()),
            fetch("/tasks").then(r => r.json()),
        ]);
        renderBots(bots, botsEl, refresh);
        renderTasks(tasks);

        if (botsCountEl)  botsCountEl.textContent  = bots.length;
        if (tasksCountEl) tasksCountEl.textContent = tasks.length;
    } catch (e) {
        console.error("refresh error:", e);
    }
}


function renderTasks(tasks) {
    tasks = [...tasks].sort((a, b) => (b.created_at || 0) - (a.created_at || 0));

    // --- фильтр ---
    const filtered = currentFilter === "all"
        ? tasks
        : tasks.filter(t => t.status === currentFilter);

    if (!filtered.length) {
        if (!tasksEl.querySelector(".empty")) {
            const msg = tasks.length
                ? `Задач со статусом <b>${currentFilter}</b> нет`
                : "Задач пока нет";
            const sub = tasks.length
                ? "Смени фильтр или поставь новую задачу"
                : "Выбери модуль выше и поставь первую задачу";
            tasksEl.innerHTML = `
                <div class="empty">
                    <div class="empty-icon">${SPHERE_SVG}</div>
                    <div class="empty-title">${msg}</div>
                    <div class="empty-sub">${sub}</div>
                </div>`;
        }
        Object.keys(taskCards).forEach(id => {
            delete taskCards[id];
            delete taskResultHash[id];
            delete taskLastPct[id];
            delete taskProgressEls[id];
        });
        return;
    }

    const emptyEl = tasksEl.querySelector(".empty");
    if (emptyEl) emptyEl.remove();

    const seen = new Set();

    filtered.forEach(t => {
        seen.add(t.task_id);
        let card = taskCards[t.task_id];

        if (!card) {
            card = document.createElement("div");
            card.className = "task";
            card.innerHTML = `
                <div class="task-head">
                    <div class="task-title">
                        <b class="type"></b>
                        <span class="target"></span>
                    </div>
                    <div class="task-side">
                        <span class="timer"></span>
                        <span class="status"></span>
                        <button class="exp" title="Экспорт результата">↓</button>
                        <button class="rm" title="Удалить задачу">✕</button>
                    </div>
                </div>
                <div class="progress"></div>
                <div class="meta"></div>
                <div class="result"></div>
            `;
            card.querySelector(".rm").onclick = () =>
                fetch(`/remove/task/${t.task_id}`, { method: "POST" }).then(refresh);
            card.querySelector(".exp").onclick = () => exportTask(t);
            tasksEl.appendChild(card);
            taskCards[t.task_id] = card;
        }

        card.className = "task " + t.status;
        card.querySelector(".type").textContent   = t.task_type;
        card.querySelector(".target").textContent = t.target;

        const statusEl = card.querySelector(".status");
        statusEl.innerHTML = `<span class="sdot"></span>${t.status}`;

        const timerEl = card.querySelector(".timer");
        if (t.status === "running" && t.started_at) {
            const sec = Math.floor(Date.now() / 1000 - t.started_at);
            timerEl.textContent = `${sec}s`;
        } else if (t.status === "done" && t.finished_at && t.started_at) {
            const sec = (t.finished_at - t.started_at).toFixed(1);
            timerEl.textContent = `${sec}s`;
        } else {
            timerEl.textContent = "";
        }

        // --- прогресс-бар: обновляем существующий, не пересоздаём ---
        const progEl = card.querySelector(".progress");
        if (t.subtasks && t.subtasks.length) {
            const done    = t.progress_done || 0;
            const failed  = t.progress_failed || 0;
            const total   = t.subtasks.length;
            const doneAll = done + failed;
            const pct     = total ? Math.round(doneAll * 100 / total) : 0;
            const running = t.status === "running";

            let refs = taskProgressEls[t.task_id];
            if (!refs || !document.body.contains(refs.pfill)) {
                // первый раз — создаём структуру
                progEl.innerHTML = `
                    <div class="pbar">
                        <div class="pfill" style="width:0%"></div>
                    </div>
                    <div class="pinfo"></div>
                `;
                refs = {
                    pbar: progEl.querySelector(".pbar"),
                    pfill: progEl.querySelector(".pfill"),
                    pinfo: progEl.querySelector(".pinfo"),
                };
                taskProgressEls[t.task_id] = refs;
                taskLastPct[t.task_id] = 0;
            }

            // включаем/выключаем блик
            refs.pbar.classList.toggle("is-running", running);

            // плавно меняем ширину
            if (taskLastPct[t.task_id] !== pct) {
                refs.pfill.style.width = pct + "%";
                taskLastPct[t.task_id] = pct;
            }

            // текст под полосой
            refs.pinfo.textContent = `${doneAll}/${total} · ok ${done} · fail ${failed}`;

            progEl.style.display = "";
        } else {
            progEl.innerHTML = "";
            progEl.style.display = "none";
            delete taskProgressEls[t.task_id];
            delete taskLastPct[t.task_id];
        }

        const metaParts = [];
        metaParts.push(t.bot_id ? `bot: ${t.bot_id}` : "bot: —");
        if (t.retries) metaParts.push(`retries: ${t.retries}`);
        if (t.error)   metaParts.push(`error: ${t.error}`);
        card.querySelector(".meta").textContent = metaParts.join(" · ");

        const resEl = card.querySelector(".result");
        let newHtml = "";

        if (t.status === "done" && Object.keys(t.result || {}).length) {
            newHtml = renderResult(t.task_type, t.result, t.subtasks_full);
        } else if (t.status === "failed") {
            newHtml = `<div class="err">${escapeHtml(t.error || "unknown error")}</div>`;
        } else if (t.status === "running") {
            newHtml = `<div class="running-indicator">Выполняется…</div>`;
        } else if (t.status === "pending" && t.subtasks && t.subtasks.length) {
            newHtml = `<div class="running-indicator">Ждёт агентов…</div>`;
        } else if (t.status === "pending" && t.retries) {
            newHtml = `<div class="warn">Ожидает перезапуска (retry ${t.retries})…</div>`;
        }

        const hash = simpleHash(newHtml);
        if (taskResultHash[t.task_id] !== hash) {
            const openStates = captureDetailsState(resEl);
            resEl.innerHTML = newHtml;
            restoreDetailsState(resEl, openStates);
            taskResultHash[t.task_id] = hash;
            attachUsernameFilters(resEl);
        }
    });

    Object.keys(taskCards).forEach(id => {
        if (!seen.has(id)) {
            taskCards[id].remove();
            delete taskCards[id];
            delete taskResultHash[id];
            delete taskLastPct[id];
            delete taskProgressEls[id];
        }
    });
}


// --- экспорт результата (JSON / CSV) ---
function exportTask(t) {
    if (!t.result || !Object.keys(t.result).length) {
        alert("Нет результата для экспорта");
        return;
    }

    const payload = {
        task_id: t.task_id,
        task_type: t.task_type,
        target: t.target,
        status: t.status,
        created_at: t.created_at,
        finished_at: t.finished_at,
        result: t.result,
    };

    // JSON
    downloadFile(
        `geryon_${t.task_type}_${t.task_id}.json`,
        JSON.stringify(payload, null, 2),
        "application/json"
    );
}


function downloadFile(filename, content, mime) {
    const blob = new Blob([content], { type: mime + ";charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}


export async function addTask() {
    const task_type = typeSel.value;
    const target = targetInput.value.trim();
    if (!target) return;

    await fetch("/task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_type, target }),
    });

    targetInput.value = "";
    updateAddBtnState();
    refresh();
}


export function initTaskControls() {
    addBtn.onclick = addTask;
    targetInput.addEventListener("keydown", e => {
        if (e.key === "Enter") addTask();
    });
    targetInput.addEventListener("input", updateAddBtnState);
    updateAddBtnState();

    // --- фильтр ---
    if (filterEl) {
        filterEl.addEventListener("click", e => {
            const btn = e.target.closest(".tf-btn");
            if (!btn) return;
            filterEl.querySelectorAll(".tf-btn").forEach(b =>
                b.classList.toggle("active", b === btn));
            currentFilter = btn.dataset.filter;
            refresh();
        });
    }
}


function updateAddBtnState() {
    const empty = !targetInput.value.trim();
    addBtn.disabled = empty;
    addBtn.classList.toggle("is-disabled", empty);
}