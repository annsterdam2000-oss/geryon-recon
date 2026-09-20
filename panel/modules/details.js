// panel/modules/details.js

export function captureDetailsState(root) {
    const states = [];
    root.querySelectorAll("details").forEach((d, i) => {
        const key = d.querySelector("summary")?.textContent?.trim() || `#${i}`;
        states.push([key, d.open]);
    });
    return states;
}

export function restoreDetailsState(root, states) {
    if (!states.length) return;
    const map = new Map(states);
    root.querySelectorAll("details").forEach((d, i) => {
        const key = d.querySelector("summary")?.textContent?.trim() || `#${i}`;
        if (map.has(key)) d.open = map.get(key);
    });
}