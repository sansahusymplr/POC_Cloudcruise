const state = {
  page: 1,
  pageSize: 10,
  practitioners: { items: [], total: 0 },
  mappings: [],
  pendingAutofill: null, // {practitioner_id, name}
};

// ---------- helpers ----------
async function api(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const text = await resp.text();
  const body = text ? JSON.parse(text) : null;
  if (!resp.ok) {
    const msg = (body && (body.detail || body.message)) || `HTTP ${resp.status}`;
    throw new Error(msg);
  }
  return body;
}

function toast(msg, kind = "info") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast" + (kind === "error" ? " error" : "");
  setTimeout(() => el.classList.add("hidden"), 4000);
}

function show(el) { el.classList.remove("hidden"); }
function hide(el) { el.classList.add("hidden"); }

// ---------- tabs ----------
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    if (btn.dataset.tab === "sessions") loadSessions();
    if (btn.dataset.tab === "mappings") loadMappings();
  });
});

// ---------- practitioners ----------
async function loadPractitioners() {
  const data = await api(`/api/practitioners?page=${state.page}&page_size=${state.pageSize}`);
  state.practitioners = data;
  const tbody = document.querySelector("#practitioners-table tbody");
  tbody.innerHTML = "";
  data.items.forEach(p => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${escape([p.first_name, p.last_name].filter(Boolean).join(" "))}</td>
      <td>${escape([p.license_type, p.license_state, p.license_number].filter(Boolean).join(" · "))}</td>
      <td>${escape([p.primary_group_name, [p.primary_city, p.primary_state].filter(Boolean).join(", ")].filter(Boolean).join(" — "))}</td>
      <td>${escape(p.primary_specialty || "")}</td>
      <td><button class="primary small" data-autofill="${p.id}">Autofill &rarr; CloudCruise</button></td>
    `;
    tbody.appendChild(tr);
  });
  const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));
  document.getElementById("page-info").textContent = `Page ${data.page} / ${totalPages} (${data.total} total)`;
  document.getElementById("prev-page").disabled = data.page <= 1;
  document.getElementById("next-page").disabled = data.page >= totalPages;
}

function escape(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

document.getElementById("prev-page").addEventListener("click", () => {
  if (state.page > 1) { state.page--; loadPractitioners(); }
});
document.getElementById("next-page").addEventListener("click", () => {
  state.page++; loadPractitioners();
});

document.querySelector("#practitioners-table tbody").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-autofill]");
  if (!btn) return;
  const id = Number(btn.dataset.autofill);
  const p = state.practitioners.items.find(x => x.id === id);
  openUrlPicker(id, [p?.first_name, p?.last_name].filter(Boolean).join(" ") || `Practitioner #${id}`);
});

// ---------- url picker ----------
async function openUrlPicker(practitionerId, name) {
  await loadMappings();
  if (!state.mappings.length) {
    toast("Add a workflow mapping first (Workflow Mappings tab)", "error");
    return;
  }
  const select = document.getElementById("picker-select");
  select.innerHTML = state.mappings
    .map(m => `<option value="${escape(m.target_url)}">${escape(m.name)} — ${escape(m.target_url)}</option>`)
    .join("");
  document.getElementById("picker-name").textContent = name;
  state.pendingAutofill = { practitioner_id: practitionerId, name };
  show(document.getElementById("url-picker"));
}

document.getElementById("picker-cancel").addEventListener("click", () => {
  hide(document.getElementById("url-picker"));
  state.pendingAutofill = null;
});

document.getElementById("picker-confirm").addEventListener("click", async () => {
  const target_url = document.getElementById("picker-select").value;
  const { practitioner_id } = state.pendingAutofill;
  hide(document.getElementById("url-picker"));
  const confirmBtn = document.getElementById("picker-confirm");
  confirmBtn.disabled = true;
  try {
    const result = await api("/api/autofill", {
      method: "POST",
      body: JSON.stringify({ practitioner_id, target_url }),
    });
    showResult(result);
    toast(result.status === "success" ? "Autofilled successfully" : `Autofill failed: ${result.error_message || ""}`, result.status === "success" ? "info" : "error");
  } catch (err) {
    showResult({ status: "failed", error_message: err.message });
    toast(err.message, "error");
  } finally {
    confirmBtn.disabled = false;
  }
});

function showResult(result) {
  document.getElementById("result-title").textContent =
    result.status === "success" ? "Autofill submitted" : "Autofill failed";
  document.getElementById("result-body").textContent = JSON.stringify(result, null, 2);
  show(document.getElementById("result-modal"));
}
document.getElementById("result-close").addEventListener("click", () => hide(document.getElementById("result-modal")));

// ---------- mappings ----------
async function loadMappings() {
  const data = await api("/api/mappings");
  state.mappings = data;
  const tbody = document.querySelector("#mappings-table tbody");
  tbody.innerHTML = "";
  data.forEach(m => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escape(m.name)}</td>
      <td>${escape(m.target_url)}</td>
      <td><code>${escape(m.workflow_id)}</code></td>
      <td><button class="danger small" data-delete-mapping="${m.id}">Delete</button></td>
    `;
    tbody.appendChild(tr);
  });
}

document.getElementById("mapping-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.currentTarget;
  const payload = {
    name: form.name.value.trim(),
    target_url: form.target_url.value.trim(),
    workflow_id: form.workflow_id.value.trim(),
  };
  try {
    await api("/api/mappings", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    toast("Mapping added");
    loadMappings();
  } catch (err) {
    toast(err.message, "error");
  }
});

document.querySelector("#mappings-table tbody").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-delete-mapping]");
  if (!btn) return;
  const id = btn.dataset.deleteMapping;
  if (!confirm("Delete this mapping?")) return;
  try {
    await api(`/api/mappings/${id}`, { method: "DELETE" });
    loadMappings();
  } catch (err) {
    toast(err.message, "error");
  }
});

// ---------- sessions ----------
async function loadSessions() {
  const data = await api("/api/sessions");
  const tbody = document.querySelector("#sessions-table tbody");
  tbody.innerHTML = "";
  data.forEach(s => {
    const tr = document.createElement("tr");
    const when = new Date(s.created_at).toLocaleString();
    const sessionCell = s.cc_session_url
      ? `<a href="${escape(s.cc_session_url)}" target="_blank">${escape(s.cc_session_id || "open")}</a>`
      : escape(s.cc_session_id || "");
    const statusClass = s.status === "success" ? "status-success" : "status-failed";
    tr.innerHTML = `
      <td>${escape(when)}</td>
      <td>#${s.practitioner_id}</td>
      <td>${escape(s.target_url)}</td>
      <td><code>${escape(s.workflow_id)}</code></td>
      <td>${sessionCell}</td>
      <td class="${statusClass}">${escape(s.status)}${s.error_message ? ` — ${escape(s.error_message)}` : ""}</td>
    `;
    tbody.appendChild(tr);
  });
}
document.getElementById("refresh-sessions").addEventListener("click", loadSessions);

// ---------- init ----------
loadPractitioners();
loadMappings();
