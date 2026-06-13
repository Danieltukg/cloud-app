/* VERTEX — клиентская логика. Чистый JS, без зависимостей. */

// База API. Тот же origin (бэкенд отдаёт и фронтенд, и /api).
// Если будешь разносить фронт и бэк по разным контейнерам/портам —
// поставь сюда абсолютный адрес, напр. "http://localhost:5000/api".
const API = "/api";

const $ = (sel) => document.querySelector(sel);
const grid = $("#grid");
const empty = $("#empty");

const state = {
  search: "",
  country: "",
  range: "",
  sort: "height_desc",
  editingId: null,
};

let debounce;

/* --- Запросы ------------------------------------------------- */

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw data;
  return data;
}

/* --- Статус соединения -------------------------------------- */

async function pingStatus() {
  const el = $("#status");
  try {
    const h = await api("/health");
    const up = h.db === "up";
    el.textContent = up ? "● база на связи" : "● база недоступна";
    el.className = "masthead__status " + (up ? "is-up" : "is-down");
  } catch {
    el.textContent = "● сервер недоступен";
    el.className = "masthead__status is-down";
  }
}

/* --- Статистика и фильтры ----------------------------------- */

function animateNumber(el, target) {
  const start = 0;
  const dur = 700;
  const t0 = performance.now();
  function step(now) {
    const p = Math.min((now - t0) / dur, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(start + (target - start) * eased).toLocaleString("ru-RU");
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

async function loadStats() {
  try {
    const s = await api("/stats");
    document.querySelectorAll("[data-key]").forEach((el) => {
      animateNumber(el, s[el.dataset.key] ?? 0);
    });
  } catch {
    /* статистика не критична */
  }
}

async function loadMeta() {
  try {
    const m = await api("/meta");
    fillSelect($("#filter-country"), m.countries, "Все страны");
    fillSelect($("#filter-range"), m.ranges, "Все хребты");
  } catch {
    /* ignore */
  }
}

function fillSelect(sel, items, placeholder) {
  const current = sel.value;
  sel.innerHTML = `<option value="">${placeholder}</option>`;
  items.forEach((it) => {
    const o = document.createElement("option");
    o.value = it;
    o.textContent = it;
    sel.appendChild(o);
  });
  sel.value = current;
}

/* --- Карточки ------------------------------------------------ */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function cardHTML(p, index) {
  const rank = String(index + 1).padStart(2, "0");
  const year = p.first_ascent_year
    ? `<span class="tag">первое восхождение · ${p.first_ascent_year}</span>`
    : "";
  return `
    <article class="card" style="animation-delay:${index * 45}ms">
      <div class="card__rank">№ ${rank} · ${esc(p.range_name)}</div>
      <h3 class="card__name">${esc(p.name)}</h3>
      <div class="card__height">${p.height_m.toLocaleString("ru-RU")}<span>м</span></div>
      <div class="card__meta">
        <span class="tag tag--glacier">${esc(p.country)}</span>
        <span class="tag">${esc(p.difficulty)}</span>
        ${year}
      </div>
      <p class="card__summary">${esc(p.summary)}</p>
      <div class="card__foot">
        <button class="card__action" data-edit="${p.id}">редактировать</button>
        <button class="card__action danger" data-del="${p.id}">удалить</button>
      </div>
    </article>`;
}

async function loadPeaks() {
  const params = new URLSearchParams();
  if (state.search) params.set("search", state.search);
  if (state.country) params.set("country", state.country);
  if (state.range) params.set("range", state.range);
  params.set("sort", state.sort);

  try {
    const peaks = await api("/peaks?" + params.toString());
    grid.innerHTML = peaks.map(cardHTML).join("");
    empty.hidden = peaks.length > 0;
  } catch {
    grid.innerHTML = "";
    empty.hidden = false;
    empty.textContent = "Не удалось загрузить данные — проверь, запущен ли бэкенд.";
  }
}

/* --- Модалка ------------------------------------------------- */

const modal = $("#modal");

function openModal(peak = null) {
  state.editingId = peak ? peak.id : null;
  $("#modal-title").textContent = peak ? "Редактировать вершину" : "Новая вершина";
  $("#f-name").value = peak?.name ?? "";
  $("#f-height").value = peak?.height_m ?? "";
  $("#f-year").value = peak?.first_ascent_year ?? "";
  $("#f-country").value = peak?.country ?? "";
  $("#f-range").value = peak?.range_name ?? "";
  $("#f-difficulty").value = peak?.difficulty ?? "Средняя";
  $("#f-summary").value = peak?.summary ?? "";
  $("#form-error").hidden = true;
  modal.hidden = false;
}

function closeModal() {
  modal.hidden = true;
  state.editingId = null;
}

async function save() {
  const payload = {
    name: $("#f-name").value.trim(),
    height_m: $("#f-height").value,
    first_ascent_year: $("#f-year").value || null,
    country: $("#f-country").value.trim(),
    range_name: $("#f-range").value.trim(),
    difficulty: $("#f-difficulty").value,
    summary: $("#f-summary").value.trim(),
  };
  const errBox = $("#form-error");
  try {
    if (state.editingId) {
      await api("/peaks/" + state.editingId, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      await api("/peaks", { method: "POST", body: JSON.stringify(payload) });
    }
    closeModal();
    await Promise.all([loadPeaks(), loadStats(), loadMeta()]);
  } catch (e) {
    const msgs = e.errors || [e.error || "Что-то пошло не так"];
    errBox.textContent = msgs.join(". ");
    errBox.hidden = false;
  }
}

async function remove(id) {
  if (!confirm("Удалить вершину из базы?")) return;
  await api("/peaks/" + id, { method: "DELETE" });
  await Promise.all([loadPeaks(), loadStats(), loadMeta()]);
}

/* --- События ------------------------------------------------- */

$("#search").addEventListener("input", (e) => {
  state.search = e.target.value.trim();
  clearTimeout(debounce);
  debounce = setTimeout(loadPeaks, 250);
});
$("#filter-country").addEventListener("change", (e) => { state.country = e.target.value; loadPeaks(); });
$("#filter-range").addEventListener("change", (e) => { state.range = e.target.value; loadPeaks(); });
$("#sort").addEventListener("change", (e) => { state.sort = e.target.value; loadPeaks(); });
$("#add-btn").addEventListener("click", () => openModal());
$("#save-btn").addEventListener("click", save);

document.querySelectorAll("[data-close]").forEach((el) =>
  el.addEventListener("click", closeModal)
);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modal.hidden) closeModal();
});

grid.addEventListener("click", async (e) => {
  const editId = e.target.dataset.edit;
  const delId = e.target.dataset.del;
  if (editId) {
    const peak = await api("/peaks/" + editId);
    openModal(peak);
  } else if (delId) {
    remove(delId);
  }
});

/* --- Старт --------------------------------------------------- */

(async function init() {
  await pingStatus();
  await Promise.all([loadStats(), loadMeta(), loadPeaks()]);
  setInterval(pingStatus, 15000);
})();
