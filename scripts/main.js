// scripts/main.js

/* ============================================================
   SCP POKÉMON ARCHIVE — main.js (TERMINAL UI v3, auto trainer sprites)
============================================================ */

let SCP_DATA = [];
let FILTERED_DATA = [];
let CURRENT_PAGE = 1;
const PAGE_SIZE = 30;

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
   SETTINGS PANEL
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

  if (SETTINGS.redactions) {
    document.body.classList.add("redactions-enabled");
  }
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
   TERMINAL OVERLAY v3 (boot + breach pulse)
============================================================ */

function setupTerminalOverlay() {
  const overlay = document.getElementById("terminal-overlay");
  const beep = document.getElementById("terminal-beep");

  if (!overlay) return;

  if (SETTINGS.overlay) {
    overlay.classList.remove("hidden");
    overlay.classList.add("crt-boot");

    if (SETTINGS.sounds && beep) {
      try {
        beep.currentTime = 0;
        beep.play();
      } catch (_) {}
    }

    setTimeout(() => {
      if (Math.random() < 0.25) {
        overlay.classList.add("breach");
        const win = overlay.querySelector(".terminal-window");
        if (win) {
          win.innerHTML = `
            <p>> ALERT: POTENTIAL SCP BREACH DETECTED</p>
            <p>> THREAT ANALYSIS: <span class="red">ELEVATED</span></p>
            <p>> RECHECK CONTAINMENT PROTOCOLS...</p>
            <p class="blink">█</p>
          `;
        }
      }
    }, 1200);

    setTimeout(() => {
      overlay.classList.remove("crt-boot");
      overlay.classList.remove("breach");
      overlay.classList.add("hidden");
    }, 3800);
  } else {
    overlay.classList.add("hidden");
  }
}

/* ============================================================
   LOAD ALL JSON FILES (POKÉMON + TRAINERS)
============================================================ */

async function loadSCPData() {
  if (SCP_DATA.length) return SCP_DATA;

  const dataFolder = "data/";
  const files = [
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

    "trainer_scp_1_10.json",
    "trainer_scp_11_20.json",
    "trainer_scp_21_30.json",
    "trainer_scp_31_40.json",
    "trainer_scp_41_50.json",
    "trainer_scp_51_60.json",
    "trainer_scp_61_70.json",
    "trainer_scp_71_80.json",
    "trainer_scp_81_90.json",
    "trainer_scp_91_100.json",
    "trainer_scp_101_110.json",
    "trainer_scp_111_120.json",
    "trainer_scp_121_130.json",
    "trainer_scp_131_140.json",
    "trainer_scp_141_151.json",
  ];

  const promises = files.map(async (file) => {
    try {
      const res = await fetch(dataFolder + file);
      if (!res.ok) return [];
      const json = await res.json();
      return json.pokemon_scp || json.trainer_scp || [];
    } catch (_) {
      return [];
    }
  });

  const results = await Promise.all(promises);
  SCP_DATA = results.flat();

  // sort by SCP item number for consistent ordering and navigation
  SCP_DATA.sort((a, b) =>
    (a.scp_item_number || "").localeCompare(b.scp_item_number || ""),
  );

  return SCP_DATA;
}

/* ============================================================
   HOME PAGE
============================================================ */

async function initHomePage() {
  const loader = document.getElementById("loader");
  if (loader) loader.textContent = "Loading SCP files...";

  await loadSCPData();

  if (loader) loader.style.display = "none";

  setupSearchFilters();
  setupSorting();
  FILTERED_DATA = SCP_DATA;
  renderSCPList();
}

/* ============================================================
   SEARCH + FILTERS
============================================================ */

function setupSearchFilters() {
  const searchInput = document.getElementById("search-input");
  const filterClass = document.getElementById("filter-class");
  const filterThreat = document.getElementById("filter-threat");

  if (!searchInput || !filterClass || !filterThreat) return;

  searchInput.addEventListener("input", applyFilters);
  filterClass.addEventListener("change", applyFilters);
  filterThreat.addEventListener("change", applyFilters);
}

function applyFilters() {
  const search = document.getElementById("search-input").value.toLowerCase();
  const classFilter = document.getElementById("filter-class").value;
  const threatFilter = document.getElementById("filter-threat").value;

  FILTERED_DATA = SCP_DATA.filter((entry) => {
    const nameMatch =
      !search ||
      entry.name?.toLowerCase().includes(search) ||
      entry.scp_item_number?.toLowerCase().includes(search);

    const classMatch = !classFilter || entry.object_class === classFilter;
    const threatMatch = !threatFilter || entry.threat_level === threatFilter;

    return nameMatch && classMatch && threatMatch;
  });

  CURRENT_PAGE = 1;
  renderSCPList();
}

/* ============================================================
   SORTING
============================================================ */

function setupSorting() {
  const controls = document.querySelector(".controls");
  if (!controls) return;

  const sortSelect = document.createElement("select");
  sortSelect.id = "sort-select";
  sortSelect.innerHTML = `
    <option value="">Sort (None)</option>
    <option value="name">Name (A–Z)</option>
    <option value="scp">SCP Number</option>
    <option value="class">Object Class</option>
    <option value="threat">Threat Level</option>
  `;

  controls.appendChild(sortSelect);

  sortSelect.addEventListener("change", () => {
    const value = sortSelect.value;

    if (value === "name") {
      FILTERED_DATA.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    } else if (value === "scp") {
      FILTERED_DATA.sort((a, b) =>
        (a.scp_item_number || "").localeCompare(b.scp_item_number || ""),
      );
    } else if (value === "class") {
      FILTERED_DATA.sort((a, b) =>
        (a.object_class || "").localeCompare(b.object_class || ""),
      );
    } else if (value === "threat") {
      FILTERED_DATA.sort((a, b) =>
        (a.threat_level || "").localeCompare(b.threat_level || ""),
      );
    }

    CURRENT_PAGE = 1;
    renderSCPList();
  });
}

/* ============================================================
   PAGINATION
============================================================ */

function renderPagination(totalPages) {
  const list = document.getElementById("scp-list");
  if (!list) return;

  const pagination = document.createElement("div");
  pagination.className = "pagination";

  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement("button");
    btn.textContent = i;
    btn.className = i === CURRENT_PAGE ? "active" : "";
    btn.addEventListener("click", () => {
      CURRENT_PAGE = i;
      renderSCPList();
    });
    pagination.appendChild(btn);
  }

  list.appendChild(pagination);
}

/* ============================================================
   RENDER SCP LIST
============================================================ */

function renderSCPList() {
  const list = document.getElementById("scp-list");
  if (!list) return;

  list.innerHTML = "";

  const start = (CURRENT_PAGE - 1) * PAGE_SIZE;
  const end = start + PAGE_SIZE;
  const pageData = FILTERED_DATA.slice(start, end);

  pageData.forEach((entry) => {
    const card = document.createElement("article");
    card.className = "scp-card flip-card";

    const objectClass = entry.object_class || "Unknown";
    const threatLevel = entry.threat_level || "Unknown";

    const isTrainer = entry.id && String(entry.id).startsWith("T");
    const isPokemon = !isTrainer;

    let visualBlock = "";
    let typeBlock = "";

    if (isPokemon) {
      const types = entry.types
        ? Object.values(entry.types).filter(Boolean)
        : [];
      if (types.length) {
        typeBlock = `
          <div class="type-box">
            ${types
              .map(
                (t) =>
                  `<img src="${getTypeIcon(t)}" class="type-icon" alt="${t}" />`,
              )
              .join("")}
          </div>
        `;
      }

      visualBlock = `
        <div class="sprite-carousel">
          <img src="${getSprite(entry.id, false, true)}" class="sprite" alt="${entry.name} front" />
          <img src="${getSprite(entry.id, true, true)}" class="sprite shiny" alt="${entry.name} shiny front" />
        </div>
        ${typeBlock}
      `;
    } else {
      const initials = getTrainerInitials(entry.name);
      const color = getTrainerColor(entry.name);
      visualBlock = `
        <div class="trainer-avatar" style="background:${color}">
          ${initials}
        </div>
      `;
    }

    const summary =
      entry.description || entry.classification || entry.behavior_notes || "";

    card.innerHTML = `
      <div class="flip-inner">
        <div class="flip-front">
          <h3>${entry.scp_item_number} — ${entry.name}</h3>
          ${visualBlock}
          <p>
            <span class="badge" data-class="${objectClass}">${objectClass}</span>
            <span class="badge" data-threat="${threatLevel}">${threatLevel}</span>
          </p>
        </div>
        <div class="flip-back">
          <p class="scp-summary">${summary}</p>
        </div>
      </div>
    `;

    card.addEventListener("click", () => {
      navigateTo(entry.id);
    });

    list.appendChild(card);
  });

  const totalPages = Math.ceil(FILTERED_DATA.length / PAGE_SIZE);
  if (totalPages > 1) renderPagination(totalPages);
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
  const numericId = Number(idParam);

  const entry =
    SCP_DATA.find((e) => e.id === idParam) || // trainers (string IDs)
    SCP_DATA.find((e) => e.id === numericId) || // pokemon (numeric IDs)
    SCP_DATA.find((e) => e.scp_item_number === idParam);

  if (!entry) {
    doc.textContent = `SCP file not found for ID: ${idParam}`;
    return;
  }

  renderViewer(entry);
}

/* ============================================================
   NAVIGATION HELPER
============================================================ */

function navigateTo(id) {
  window.location.href = `viewer.html?id=${encodeURIComponent(id)}`;
}

/* ============================================================
   SPRITE + TYPE ICON HELPERS
============================================================ */

function getSprite(id, shiny = false, front = true) {
  const base = shiny ? "assets/shiny" : "assets/normal";
  const side = front ? "front" : "back";
  return `${base}/${side}/${id}.png`;
}

function getTypeIcon(type) {
  return `assets/types/${String(type).toLowerCase()}.png`;
}

/* ============================================================
   TRAINER SPRITE HELPERS (AUTO-GENERATED)
============================================================ */

function getTrainerInitials(name = "") {
  const parts = name.trim().split(/\s+/);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (
    parts[0].charAt(0).toUpperCase() +
    parts[parts.length - 1].charAt(0).toUpperCase()
  );
}

function getTrainerColor(name = "") {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = (hash << 5) - hash + name.charCodeAt(i);
    hash |= 0;
  }
  const hue = Math.abs(hash) % 360;
  return `radial-gradient(circle at 30% 30%, hsl(${hue}, 80%, 60%), #111)`;
}

/* ============================================================
   VIEWER RENDERING
============================================================ */

function renderViewer(entry) {
  const doc = document.getElementById("scp-doc");
  if (!doc) return;

  const objectClass = entry.object_class || "Unknown";
  const threatLevel = entry.threat_level || "Unknown";

  const abilities = entry.abilities || [];
  const logs = entry.addendum_logs || [];

  const isTrainer = entry.id && String(entry.id).startsWith("T");
  const isPokemon = !isTrainer;

  let typeValues = [];
  if (isPokemon && entry.types) {
    typeValues = Object.values(entry.types).filter(Boolean);
  }

  const spriteSection = isPokemon
    ? `
      <div class="sprite-carousel">
        <img src="${getSprite(entry.id, false, true)}" class="sprite" alt="${entry.name} front" />
        <img src="${getSprite(entry.id, true, true)}" class="sprite shiny" alt="${entry.name} shiny front" />
        <img src="${getSprite(entry.id, false, false)}" class="sprite back" alt="${entry.name} back" />
        <img src="${getSprite(entry.id, true, false)}" class="sprite shiny back" alt="${entry.name} shiny back" />
      </div>
    `
    : "";

  const typeSection =
    isPokemon && typeValues.length
      ? `
      <div class="type-box">
        ${typeValues
          .map(
            (t) =>
              `<img src="${getTypeIcon(t)}" class="type-icon" alt="${t}" />`,
          )
          .join("")}
      </div>
    `
      : "";

  const trainerAvatarSection = isTrainer
    ? (() => {
        const initials = getTrainerInitials(entry.name);
        const color = getTrainerColor(entry.name);
        return `
          <div class="trainer-avatar-large" style="background:${color}">
            ${initials}
          </div>
        `;
      })()
    : "";

  // compute prev/next based on sorted SCP_DATA
  const index = SCP_DATA.indexOf(entry);
  let prevId = null;
  let nextId = null;
  if (index !== -1) {
    const prevEntry = SCP_DATA[(index - 1 + SCP_DATA.length) % SCP_DATA.length];
    const nextEntry = SCP_DATA[(index + 1) % SCP_DATA.length];
    prevId = prevEntry.id;
    nextId = nextEntry.id;
  }

  const navSection =
    prevId != null && nextId != null
      ? `
    <div class="doc-nav">
      <button class="nav-btn" onclick="navigateTo('${prevId}')">◀ Previous</button>
      <button class="nav-btn" onclick="navigateTo('${nextId}')">Next ▶</button>
    </div>
  `
      : "";

  doc.innerHTML = `
    <h2>${entry.scp_item_number} — ${entry.name}</h2>

    ${spriteSection}
    ${trainerAvatarSection}
    ${typeSection}

    <p><strong>Object Class:</strong> <span class="badge" data-class="${objectClass}">${objectClass}</span></p>
    <p><strong>Threat Level:</strong> <span class="badge" data-threat="${threatLevel}">${threatLevel}</span></p>

    ${entry.classification ? `<p><strong>Classification:</strong> ${entry.classification}</p>` : ""}

    ${
      entry.description ? `<h3>Description</h3><p>${entry.description}</p>` : ""
    }

    ${
      entry.special_containment_procedures
        ? `<h3>Special Containment Procedures</h3><p>${entry.special_containment_procedures}</p>`
        : entry.containment_advisories
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
    ${navSection}
  `;
}
