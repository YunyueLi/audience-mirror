"use strict";

const root = document.documentElement;
const themeButton = document.getElementById("system-theme");
const toast = document.getElementById("system-toast");

function syncThemeControl() {
  const dark = root.dataset.theme === "dark";
  themeButton?.setAttribute("aria-label", dark ? "切换到浅色主题" : "切换到深色主题");
  themeButton?.setAttribute("title", dark ? "切换到浅色主题" : "切换到深色主题");
  const meta = document.getElementById("theme-color");
  if (meta) meta.content = dark ? "#0a0d11" : "#f5f3ee";
}

themeButton?.addEventListener("click", () => {
  root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
  try { localStorage.setItem("audience-mirror-theme", root.dataset.theme); } catch {}
  syncThemeControl();
});

document.querySelectorAll(".lab-tabs [role='tab']").forEach((tab, index, tabs) => {
  tab.addEventListener("click", () => {
    tabs.forEach(candidate => candidate.setAttribute("aria-selected", String(candidate === tab)));
  });
  tab.addEventListener("keydown", event => {
    let next = null;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    if (next === null) return;
    event.preventDefault();
    tabs[next].click();
    tabs[next].focus();
  });
});

let toastTimer = null;
function setToast(visible) {
  toast?.classList.toggle("is-visible", visible);
  if (visible) {
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => setToast(false), 3600);
  }
}
document.getElementById("show-system-toast")?.addEventListener("click", () => setToast(true));
toast?.querySelector(".message-dismiss")?.addEventListener("click", () => setToast(false));
syncThemeControl();
