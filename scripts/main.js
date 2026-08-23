/* ============================================================
   SCP POKÉMON ARCHIVE — main.js
   Handles:
   - Settings (sounds, overlay, redactions)
   - Terminal overlay
   - Home page: list, search, filters, navigation
   - Viewer page: single SCP file rendering
============================================================ */

let SCP_DATA = [];
const SETTINGS = {
  sounds: false,
  overlay: false,
  redactions: false,
};

/* ============================================================
   ENTRY POINT
============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  setupSettingsPanel();
  setupTerminalOverlay();

  const body = document.body;

  if (body.classList.contains("page-home")) {
    initHomePage();
  } else if (body.classList.contains("page-viewer")) {
    initViewerPage();
  }
});

/* ============================================================
   SETTINGS
============================================================ */

function loadSettings() {
  SETTINGS.sounds = localStorage.getItem("scp_sounds") === "true";
  SETTINGS.overlay = localStorage.getItem("scp_overlay") === "true";
  SETTINGS.redactions = localStorage.getItem("scp_redactions") === "true";

  const sounds = document.getElementById("setting-sounds");
  const overlay = document.getElementById("setting-overlay");
  const redactions = document.getElementById("setting-redactions");

  if (sounds) sounds.checked = SETTINGS.sounds;
  if (overlay) overlay.checked = SETTINGS.overlay;
  if (redactions) redactions.checked = SETTINGS.redactions;
}

function setupSettingsPanel() {
  const panel = document.getElementById("settings-panel");
  const toggle = document.getElementById("settings-toggle");
  const close = document.getElementById("settings-close");

  if (!panel || !toggle || !close) return;

  toggle.addEventListener("click", () => panel.classList.remove("hidden"));
  close.addEventListener("click", () => panel.classList.add("hidden"));

  const sounds = document.getElementById("setting-sounds");
  const overlay = document.getElementById("setting-overlay");
  const redactions = document.getElementById("setting-redactions");

  if (sounds) {
    sounds.addEventListener("change", (e) => {
      SETTINGS.sounds = e.target.checked;
      localStorage.setItem("scp_sounds", SETTINGS.sounds);
    });
  }

  if (overlay) {
    overlay.addEventListener("change", (e) => {
      SETTINGS.overlay = e.target.checked;
      localStorage.setItem("scp_overlay", SETTINGS.overlay);
    });
  }

  if (redactions) {
    redactions.addEventListener("change", (e) => {
      SETTINGS.redactions = e.target.checked;
      localStorage.setItem("scp_redactions", SETTINGS.redactions);
      document.body.classList.toggle("redactions-enabled", SETTINGS.redactions);
    });
  }
}

/* ============================================================
   TERMINAL OVERLAY
============================================================ */

function setupTerminalOverlay() {
  const overlay = document.getElementById("terminal-overlay");
  const beep = document.getElementById("terminal-beep");

  if (!overlay) return;

  if (SETTINGS.overlay) {
    overlay.classList.remove("hidden");
    if (SETTINGS.sounds && beep) {
      try {
        beep.currentTime = 0;
        beep.play();
      } catch (_) {}
    }
    setTimeout(() => overlay.classList.add("hidden"), 4000);
  } else {
    overlay.classList.add("hidden");
  }
}

/* ============================================================
   DATA LOADING
============================================================ */

async function loadSCPData() {
  if (SCP_DATA.length) return SCP_DATA;

  try {
    const res = await fetch("data/scp_pokemon.json");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const json = await res.json();
    SCP_DATA = Array.isArray(json) ? json : json.scp_pokemon || [];
  } catch (err) {
    console.error("Failed to load SCP data:", err);
  }

  return SCP_DATA;
}

/* ============================================================
   HOME PAGE
============================================================ */

async function initHomePage() {
  const loader = document.getElementById("loader");
  const list = document.getElementById("scp-list");

  if (!loader || !list) return;

  loader.textContent = "Loading SCP files...";

  await loadSCPData();

  loader.style.display = "none";
  setupSearchFilters();
  renderSCPList();
}

function setupSearchFilters() {
  const searchInput = document.getElementById("search-input");
  const filterClass = document.getElementById("filter-class");
  const filterThreat = document.getElementById("filter-threat");

  if (searchInput) searchInput.addEventListener("input", renderSCPList);
  if (filterClass) filterClass.addEventListener("change", renderSCPList);
  if (filterThreat) filterThreat.addEventListener("change", renderSCPList);
}

function renderSCPList() {
  const list = document.getElementById("scp-list");
  if (!list) return;

  list.innerHTML = "";

  const search = (
    document.getElementById("search-input")?.value || ""
  ).toLowerCase();
  const classFilter = document.getElementById("filter-class")?.value || "";
  const threatFilter = document.getElementById("filter-threat")?.value || "";

  SCP_DATA.forEach((entry) => {
    const nameMatch =
      !search ||
      entry.name?.toLowerCase().includes(search) ||
      entry.scp_item_number?.toLowerCase().includes(search);

    const classMatch = !classFilter || entry.object_class === classFilter;
    const threatMatch = !threatFilter || entry.threat_level === threatFilter;

    if (!nameMatch || !classMatch || !threatMatch) return;

    const card = document.createElement("article");
    card.className = "scp-card";

    const objectClass = entry.object_class || "Unknown";
    const threatLevel = entry.threat_level || "Unknown";

    card.innerHTML = `
      <h3>${entry.scp_item_number || "SCP-????"} — ${entry.name || "Unknown Entity"}</h3>
      <p>
        <span class="badge" data-class="${objectClass}">${objectClass}</span>
        <span class="badge" data-threat="${threatLevel}">${threatLevel}</span>
      </p>
      <p class="scp-summary">${entry.description || "No description available."}</p>
    `;

    card.addEventListener("click", () => {
      const id = entry.id || entry.scp_item_number;
      if (id) window.location.href = `viewer.html?id=${encodeURIComponent(id)}`;
    });

    list.appendChild(card);
  });

  if (!list.children.length) {
    const empty = document.createElement("p");
    empty.textContent = "No SCP files match the current filters.";
    list.appendChild(empty);
  }
}

/* ============================================================
   VIEWER PAGE
============================================================ */

async function initViewerPage() {
  const doc = document.getElementById("scp-doc");
  if (!doc) return;

  await loadSCPData();

  const params = new URLSearchParams(window.location.search);
  const idParam = params.get("id");

  if (!idParam) {
    doc.textContent = "No SCP ID specified.";
    return;
  }

  const entry =
    SCP_DATA.find((e) => e.id === idParam) ||
    SCP_DATA.find((e) => e.scp_item_number === idParam);

  if (!entry) {
    doc.textContent = `SCP file not found for ID: ${idParam}`;
    return;
  }

  renderViewer(entry);
}

function renderViewer(entry) {
  const doc = document.getElementById("scp-doc");
  if (!doc) return;

  const objectClass = entry.object_class || "Unknown";
  const threatLevel = entry.threat_level || "Unknown";

  const abilities = Array.isArray(entry.abilities) ? entry.abilities : [];
  const logs = Array.isArray(entry.addendum_logs) ? entry.addendum_logs : [];

  doc.innerHTML = `
    <h2>${entry.scp_item_number || "SCP-????"} — ${entry.name || "Unknown Entity"}</h2>

    <p>
      <strong>Object Class:</strong>
      <span class="badge" data-class="${objectClass}">${objectClass}</span>
    </p>
    <p>
      <strong>Threat Level:</strong>
      <span class="badge" data-threat="${threatLevel}">${threatLevel}</span>
    </p>

    ${
      entry.classification
        ? `<p><strong>Classification:</strong> ${entry.classification}</p>`
        : ""
    }

    ${
      entry.description ? `<h3>Description</h3><p>${entry.description}</p>` : ""
    }

    ${
      entry.containment_advisories
        ? `<h3>Containment Advisories</h3><p>${entry.containment_advisories}</p>`
        : ""
    }

    ${
      entry.behavior_notes
        ? `<h3>Behavior Notes</h3><p>${entry.behavior_notes}</p>`
        : ""
    }

    ${
      abilities.length
        ? `<h3>Abilities</h3><ul>${abilities
            .map((a) => `<li>${a}</li>`)
            .join("")}</ul>`
        : ""
    }

    ${
      logs.length
        ? `<h3>Addendum Logs</h3><ul>${logs
            .map((l) => `<li>${l}</li>`)
            .join("")}</ul>`
        : ""
    }

    <p><a href="index.html">&larr; Return to Archive</a></p>
  `;
}
