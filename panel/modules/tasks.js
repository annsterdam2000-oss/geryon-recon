// panel/modules/tasks.js
import { renderBots } from "./bots.js";
import { renderResult } from "./renders/index.js";
import { captureDetailsState, restoreDetailsState } from "./details.js";
import { escapeHtml, simpleHash } from "./utils.js";
import { attachUsernameFilters } from "./renders/username.js";

const taskCards = {};
const taskResultHash = {};

const botsEl   = document.getElementById("bots");
const tasksEl  = document.getElementById("tasks");
const typeSel  = document.getElementById("task-type");
const targetInput = document.getElementById("task-target");
const addBtn   = document.getElementById("task-add");

const botsCountEl  = document.getElementById("bots-count");
const tasksCountEl = document.getElementById("tasks-count");


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
    const seen = new Set();

    tasks.forEach(t => {
        seen.add(t.task_id);
        let card = taskCards[t.task_id];

        if (!card) {
            card = document.createElement("div");
            card.className = "task";
            card.innerHTML = `
                <div class="row">
                    <b class="type"></b>
                    <span class="target"></span>
                    <span class="timer"></span>
                    <span class="status"></span>
                    <button class="rm" title="Удалить задачу">✕</button>
                </div>
                <div class="progress"></div>
                <div class="meta"></div>
                <div class="result"></div>
            `;
            card.querySelector(".rm").onclick = () =>
                fetch(`/remove/task/${t.task_id}`, { method: "POST" }).then(refresh);
            tasksEl.appendChild(card);
            taskCards[t.task_id] = card;
        }

        card.className = "task " + t.status;
        card.querySelector(".type").textContent   = t.task_type;
        card.querySelector(".target").textContent = t.target;
        card.querySelector(".status").textContent = t.status;

        // --- таймер ---
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

        // --- прогресс-бар ---
        const progEl = card.querySelector(".progress");
        if (t.subtasks && t.subtasks.length) {
            const done    = t.progress_done || 0;
            const failed  = t.progress_failed || 0;
            const total   = t.subtasks.length;
            const doneAll = done + failed;
            const pct     = total ? Math.round(doneAll * 100 / total) : 0;
            progEl.innerHTML = `
                <div class="pbar"><div class="pfill" style="width:${pct}%"></div></div>
                <div class="pinfo">${doneAll}/${total} · ok ${done} · fail ${failed}</div>
            `;
            progEl.style.display = "";
        } else {
            progEl.innerHTML = "";
            progEl.style.display = "none";
        }

        // --- мета ---
        const metaParts = [];
        metaParts.push(t.bot_id ? `bot: ${t.bot_id}` : "bot: —");
        if (t.retries) metaParts.push(`retries: ${t.retries}`);
        if (t.error)   metaParts.push(`error: ${t.error}`);
        card.querySelector(".meta").textContent = metaParts.join(" · ");

        // --- результат ---
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

        // --- точечное обновление, чтобы не сбивать раскрытые details ---
        const hash = simpleHash(newHtml);
        if (taskResultHash[t.task_id] !== hash) {
            const openStates = captureDetailsState(resEl);
            resEl.innerHTML = newHtml;
            restoreDetailsState(resEl, openStates);
            taskResultHash[t.task_id] = hash;
            attachUsernameFilters(resEl);
        }
    });

    // --- удаляем карточки, которых больше нет ---
    Object.keys(taskCards).forEach(id => {
        if (!seen.has(id)) {
            taskCards[id].remove();
            delete taskCards[id];
            delete taskResultHash[id];
        }
    });
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
    refresh();
}


export function initTaskControls() {
    addBtn.onclick = addTask;
    targetInput.addEventListener("keydown", e => {
        if (e.key === "Enter") addTask();
    });
}