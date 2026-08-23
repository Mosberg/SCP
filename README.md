# **SCPdex**

_A complete SCP‑Foundation classification of all 151 Generation I Pokémon, rewritten as anomalous entities._

---

## **📘 Overview**

The **SCPdex** is a comprehensive dataset that reimagines all **151 Generation I Pokémon** as SCP Foundation anomalies.  
Each entry is written in a **Hybrid SCP style** — blending:

- Clinical containment documentation
- Horror and anomalous behavior
- Scientific analysis
- Narrative addenda

The result is a fully structured JSON SCP database suitable for:

- Worldbuilding
- Game development
- Perchance generators
- SCP‑themed Pokédex tools
- AI‑driven content systems
- Interactive fiction engines

This repository contains **all 151 SCP entries**, each with unique containment procedures, descriptions, behavior notes, and addendum logs.

---

## **📂 Project Structure**

```
/
├── data/
│   ├── pokemon_scp_1_10.json
│   ├── pokemon_scp_11_20.json
│   ├── pokemon_scp_21_30.json
│   ├── ...
│   ├── pokemon_scp_141_151.json
│   └── scpdex_master.json (optional combined file)
│
├── README.md
└── LICENSE (optional)
```

Each batch file contains **10 SCP entries**, except the final file (141–151).

All entries follow the same schema.

---

## **📐 JSON Schema**

Every SCP entity follows this structure:

```json
{
  "id": 1,
  "name": "Bulbasaur",
  "scp_item_number": "SCP-0001",
  "types": {
    "type_1": "grass",
    "type_2": "poison"
  },
  "object_class": "Euclid",
  "threat_level": "Yellow",
  "special_containment_procedures": "…",
  "description": "…",
  "behavior_notes": "…",
  "addendum_logs": ["Addendum 0001-A: …", "Addendum 0001-B: …"]
}
```

### **Field Breakdown**

- **id**  
  National Pokédex number (1–151)

- **name**  
  Pokémon name

- **scp_item_number**  
  SCP designation (SCP‑0001 → SCP‑0151)

- **types**  
  Primary and secondary typing

- **object_class**  
  SCP classification (Safe, Euclid, Keter, Apollyon, Thaumiel)

- **threat_level**  
  Color-coded danger rating (Green → Black)

- **special_containment_procedures**  
  SCP‑style containment instructions

- **description**  
  Biological/anomalous overview

- **behavior_notes**  
  Behavioral tendencies and triggers

- **addendum_logs**  
  Incident reports, observations, or narrative expansions

---

## **🧪 Example Entry**

Here’s a sample SCPdex entry (Bulbasaur):

```json
{
  "id": 1,
  "name": "Bulbasaur",
  "scp_item_number": "SCP-0001",
  "types": { "type_1": "grass", "type_2": "poison" },
  "object_class": "Euclid",
  "threat_level": "Yellow",
  "special_containment_procedures": "SCP-0001 is to be contained in a reinforced terrarium with automated humidity and light-cycle control...",
  "description": "SCP-0001 resembles a small quadrupedal reptile with a plant-like growth on its back...",
  "behavior_notes": "Generally docile and responsive to calm interaction...",
  "addendum_logs": [
    "Addendum 0001-A: Luminosity increased in sync with elevated heart rates of nearby personnel.",
    "Addendum 0001-B: SCP-0001 burrowed partially through substrate during a containment lapse."
  ]
}
```

---

## **🔧 Usage**

You can use the SCPdex dataset for:

### **Game Development**

- SCP‑themed Pokédex
- Horror RPG bestiary
- Procedural anomaly generation
- AI‑driven NPC behavior systems

### **Worldbuilding**

- SCP Foundation fan projects
- Alternate universe Pokémon lore
- Narrative SCP logs and incident reports

### **AI / Generators**

- Perchance generators
- ChatGPT / Copilot SCP‑style responses
- JSON‑driven content pipelines

### **Modding**

- Custom SCP‑Pokémon mods
- Tabletop RPG supplements
- Interactive fiction engines

---

## **📦 Combining All Files**

If you want a single master file, you can merge all JSON batches into:

```
data/scpdex_master.json
```

Structure:

```json
{
  "pokemon_scp": [
    { ...151 entries... }
  ]
}
```

---

## **🧭 Design Philosophy**

The SCPdex follows these principles:

### **1. Respect the SCP Tone**

Every entry blends:

- Clinical documentation
- Horror elements
- Scientific analysis
- Narrative storytelling

### **2. Respect Pokémon Identity**

Each SCP entry:

- Preserves the Pokémon’s core traits
- Reinterprets abilities as anomalies
- Expands behavior into SCP‑style incidents

### **3. Consistent Formatting**

All 151 entries follow identical structure for:

- Parsing
- Modding
- Automation
- AI integration

---

## **📜 Licensing**

If you plan to publish or distribute this dataset, ensure compliance with:

- Pokémon IP guidelines
- SCP Foundation Creative Commons (CC BY-SA 3.0)
- Your own project’s license

This README does not grant rights to redistribute copyrighted Pokémon assets.

---

## **🧩 Future Extensions**

Potential expansions include:

- **SCPdex Gen II–IX**
- **Mega Evolutions / Regional Forms**
- **SCP Incident Reports**
- **SCPdex Web Viewer**
- **Perchance SCPdex Generator**
- **SCPdex API**
- **SCPdex Game / Simulation**

If you want any of these, I can generate them.

---

## **🎉 Completion**

All **151 SCP entries** are now fully documented and ready for use.
