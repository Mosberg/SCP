// ------------------------------
// CONFIG
// ------------------------------
const DATA_FILES = [
  "pokemon_scp_1_10.json",
  "pokemon_scp_11_20.json",
  "pokemon_scp_21_30.json",
  "pokemon_scp_31_40.json",
  "pokemon_scp_41_50.json",
  "pokemon_scp_51_60.json",
  "pokemon_scp_61_70.json",
  "pokemon_scp_71_80.json",
  "pokemon_scp_81_90.json",
  "pokemon_scp_91_100.json",
  "pokemon_scp_101_110.json",
  "pokemon_scp_111_120.json",
  "pokemon_scp_121_130.json",
  "pokemon_scp_131_140.json",
  "pokemon_scp_141_151.json",
];

const DATA_PATH = "data";

let ALL_SCP = [];

const SETTINGS_KEY = "scp_pokemon_settings";

let SETTINGS = {
  sounds: false,
  overlay: true,
  redactionsReveal: true,
};

// ------------------------------
// COLOR MAPS
// ------------------------------
const CLASS_COLORS = {
  Safe: "#4CAF50",
  Euclid: "#FFC107",
  Keter: "#F44336",
  Apollyon: "#9C27B0",
  Thaumiel: "#03A9F4",
  Unknown: "#777",
};

const THREAT_COLORS = {
  Green: "#4CAF50",
  Yellow: "#FFEB3B",
  Orange: "#FF9800",
  Red: "#F44336",
  Crimson: "#B71C1C",
  Black: "#000000",
  Blue: "#2196F3",
  Unknown: "#777",
};

function badgeColor(value, map) {
  return map[value] || "#555";
}

// ------------------------------
// IMAGE HELPERS
// ------------------------------
function imagePath(id, variant, side) {
  return `assets/${variant}/${side}/${id}.png`;
}

function typeIcon(type) {
  return type ? `assets/types/${type}.png` : "";
}

// ------------------------------
// SETTINGS
// ------------------------------
function loadSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      SETTINGS = { ...SETTINGS, ...parsed };
    }
  } catch (e) {}
}

function saveSettings() {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS));
}

function applySettingsToUI() {
  const sounds = document.getElementById("setting-sounds");
  const overlay = document.getElementById("setting-overlay");
  const redactions = document.getElementById("setting-redactions");

  if (sounds) sounds.checked = SETTINGS.sounds;
  if (overlay) overlay.checked = SETTINGS.overlay;
  if (redactions) redactions.checked = SETTINGS.redactionsReveal;

  document.body.classList.toggle(
    "reveal-redactions",
    SETTINGS.redactionsReveal,
  );
}

function initSettingsPanel() {
  const toggle = document.getElementById("settings-toggle");
  const panel = document.getElementById("settings-panel");
  const close = document.getElementById("settings-close");

  if (!toggle || !panel || !close) return;

  toggle.addEventListener("click", () => {
    panel.classList.toggle("hidden");
  });

  close.addEventListener("click", () => {
    panel.classList.add("hidden");
  });

  const sounds = document.getElementById("setting-sounds");
  const overlay = document.getElementById("setting-overlay");
  const redactions = document.getElementById("setting-redactions");

  if (sounds) {
    sounds.addEventListener("change", () => {
      SETTINGS.sounds = sounds.checked;
      saveSettings();
    });
  }

  if (overlay) {
    overlay.addEventListener("change", () => {
      SETTINGS.overlay = overlay.checked;
      saveSettings();
    });
  }

  if (redactions) {
    redactions.addEventListener("change", () => {
      SETTINGS.redactionsReveal = redactions.checked;
      document.body.classList.toggle(
        "reveal-redactions",
        SETTINGS.redactionsReveal,
      );
      saveSettings();
    });
  }
}

// ------------------------------
// TERMINAL OVERLAY
// ------------------------------
function showUnauthorizedOverlay(duration = 5000) {
  if (!SETTINGS.overlay) return;

  const overlay = document.getElementById("terminal-overlay");
  if (!overlay) return;

  overlay.classList.remove("hidden");

  if (SETTINGS.sounds) {
    const beep = document.getElementById("terminal-beep");
    if (beep) {
      beep.currentTime = 0;
      beep.play().catch(() => {});
    }
  }

  setTimeout(() => overlay.classList.add("hidden"), duration);
}

// ------------------------------
// LOAD ALL JSON FILES (MULTI-ENTITY)
// ------------------------------
async function loadAllSCP() {
  const results = [];

  for (const file of DATA_FILES) {
    try {
      const res = await fetch(`${DATA_PATH}/${file}`);
      const json = await res.json();
      if (Array.isArray(json.pokemon_scp)) {
        results.push(...json.pokemon_scp);
      }
    } catch (err) {
      console.warn("Error loading file:", file, err);
    }
  }

  results.sort((a, b) => a.id - b.id);
  ALL_SCP = results;
  return results;
}

// ------------------------------
// HOMEPAGE RENDER + SEARCH/FILTER
// ------------------------------
async function renderHome() {
  const listEl = document.getElementById("scp-list");
  const loader = document.getElementById("loader");
  const searchInput = document.getElementById("search-input");
  const filterClass = document.getElementById("filter-class");
  const filterThreat = document.getElementById("filter-threat");

  const data = await loadAllSCP();
  loader.style.display = "none";

  function applyFilters() {
    const q = searchInput.value.trim().toLowerCase();
    const cls = filterClass.value;
    const thr = filterThreat.value;

    const filtered = data.filter((entry) => {
      const matchesSearch =
        !q ||
        entry.name.toLowerCase().includes(q) ||
        entry.scp_item_number.toLowerCase().includes(q);

      const matchesClass = !cls || entry.object_class === cls;
      const matchesThreat = !thr || entry.threat_level === thr;

      return matchesSearch && matchesClass && matchesThreat;
    });

    if (!filtered.length) {
      showUnauthorizedOverlay(3000);
    }

    renderList(filtered);
  }

  function renderList(entries) {
    listEl.innerHTML = "";
    entries.forEach((entry) => {
      const item = document.createElement("div");
      item.className = "scp-item";

      const classColor = badgeColor(entry.object_class, CLASS_COLORS);
      const threatColor = badgeColor(entry.threat_level, THREAT_COLORS);

      item.innerHTML = `
        <div class="scp-item-header">
          <span class="scp-item-number">${entry.scp_item_number}</span>
          <span class="scp-item-name">${entry.name}</span>
        </div>
        <p>
          Object Class:
          <span class="badge" style="background:${classColor}">
            ${entry.object_class}
          </span>
        </p>
        <p>
          Threat Level:
          <span class="badge" style="background:${threatColor}">
            ${entry.threat_level}
          </span>
        </p>
        <button onclick="openDoc(${entry.id})">Open Classified File</button>
      `;

      listEl.appendChild(item);
    });
  }

  searchInput.addEventListener("input", applyFilters);
  filterClass.addEventListener("change", applyFilters);
  filterThreat.addEventListener("change", applyFilters);

  applyFilters();
}

function openDoc(id) {
  document.body.classList.add("page-transition-out");
  setTimeout(() => {
    window.location.href = `viewer.html?id=${id}`;
  }, 250);
}

// ------------------------------
// DOCUMENT VIEWER RENDER
// ------------------------------
async function renderDocument() {
  if (!ALL_SCP.length) {
    await loadAllSCP();
  }

  const params = new URLSearchParams(window.location.search);
  const id = Number(params.get("id"));

  const entryIndex = ALL_SCP.findIndex((e) => e.id === id);
  const entry = ALL_SCP[entryIndex];
  const doc = document.getElementById("scp-doc");

  if (!entry) {
    doc.innerHTML = `<p>FILE NOT FOUND — ID ${id}</p>`;
    showUnauthorizedOverlay(4000);
    return;
  }

  const classColor = badgeColor(entry.object_class, CLASS_COLORS);
  const threatColor = badgeColor(entry.threat_level, THREAT_COLORS);

  const prevId =
    entryIndex > 0
      ? ALL_SCP[entryIndex - 1].id
      : ALL_SCP[ALL_SCP.length - 1].id;
  const nextId =
    entryIndex < ALL_SCP.length - 1
      ? ALL_SCP[entryIndex + 1].id
      : ALL_SCP[0].id;

  doc.innerHTML = `
    <div class="doc-nav">
      <button class="nav-btn" onclick="navigateTo(${prevId})">◀ Previous</button>
      <button class="nav-btn" onclick="navigateTo(${nextId})">Next ▶</button>
    </div>
    <div class="doc-header">
      <div class="doc-title-row">
        <h1>${entry.scp_item_number}</h1>
        <span class="doc-tag">CLASSIFIED</span>
      </div>
      <h2>${entry.name}</h2>
      <p>
        Object Class:
        <span class="badge" style="background:${classColor}">
          ${entry.object_class}
        </span>
      </p>
      <p>
        Threat Level:
        <span class="badge" style="background:${threatColor}">
          ${entry.threat_level}
        </span>
      </p>

      <div class="type-icons">
        ${
          entry.types?.type_1
            ? `<img src="${typeIcon(entry.types.type_1)}" alt="${entry.types.type_1}">`
            : ""
        }
        ${
          entry.types?.type_2
            ? `<img src="${typeIcon(entry.types.type_2)}" alt="${entry.types.type_2}">`
            : ""
        }
      </div>
    </div>

    <div class="doc-section">
      <h3>Special Containment Procedures</h3>
      <p class="${entry.special_containment_procedures ? "redacted" : "redacted"}">
        ${entry.special_containment_procedures || "REDACTED"}
      </p>
    </div>

    <div class="doc-section">
      <h3>Description</h3>
      <p class="${entry.description ? "redacted" : "redacted"}">
        ${entry.description || "REDACTED"}
      </p>
    </div>

    <div class="doc-section">
      <h3>Behavior Notes</h3>
      <p>${entry.behavior_notes || "No behavioral notes recorded."}</p>
    </div>

    <div class="doc-section">
      <h3>Addendum Logs</h3>
      <ul>
        ${
          (entry.addendum_logs || [])
            .map((log) => `<li class="redacted">${log}</li>`)
            .join("") || "<li>No addenda on file.</li>"
        }
      </ul>
    </div>

    <div class="doc-images">
      <h3>Images</h3>
      <div class="img-row">
        <div>
          <h4>Normal — Front</h4>
          <img src="${imagePath(entry.id, "normal", "front")}" alt="${entry.name} Normal Front">
        </div>
        <div>
          <h4>Normal — Back</h4>
          <img src="${imagePath(entry.id, "normal", "back")}" alt="${entry.name} Normal Back">
        </div>

        <div>
          <h4>Shiny — Front</h4>
          <img src="${imagePath(entry.id, "shiny", "front")}" alt="${entry.name} Shiny Front">
        </div>
        <div>
          <h4>Shiny — Back</h4>
          <img src="${imagePath(entry.id, "shiny", "back")}" alt="${entry.name} Shiny Back">
        </div>
      </div>
    </div>

    <div class="doc-nav">
      <button class="nav-btn" onclick="navigateTo(${prevId})">◀ Previous</button>
      <button class="nav-btn" onclick="navigateTo(${nextId})">Next ▶</button>
    </div>

    <button class="back-btn" onclick="goBack()">Return to Archive</button>
  `;
}

function navigateTo(id) {
  document.body.classList.add("page-transition-out");
  setTimeout(() => {
    window.location.href = `viewer.html?id=${id}`;
  }, 250);
}

function goBack() {
  document.body.classList.add("page-transition-out");
  setTimeout(() => {
    window.location.href = "index.html";
  }, 250);
}

// ------------------------------
// ROUTING
// ------------------------------
window.onload = () => {
  loadSettings();
  applySettingsToUI();
  initSettingsPanel();

  if (document.querySelector(".page-home")) renderHome();
  if (document.querySelector(".page-viewer")) renderDocument();
};
