# SCP-Pokémon Anomaly Archive

A framework-free, browser-based archive for displaying Pokémon data as classified SCP-style anomaly dossiers.

The system dynamically loads multiple JSON records, provides archive search and filtering, and generates individual document pages with containment information, anomaly details, Pokémon metadata, and sprite records.

## Features

- Dynamic loading of multiple JSON files.
- SCP-style classified-document interface.
- Search by:
  - Record ID.
  - Title.
  - Description.
  - Pokémon species.
  - Form.
  - Type.
  - Category.
  - Custom tags.
- Filter by object class.
- Filter by Pokémon category.
- Sort by:
  - Designation ascending.
  - Designation descending.
  - Species A–Z.
  - Species Z–A.
  - Object class.
  - Recently updated.
  - Favorites first.
- Persistent favorites using `localStorage`.
- Persistent custom tags using `localStorage`.
- Favorites-only mode.
- Random Pokémon button.
- Previous and next document navigation.
- Navigation respects the current search and filter results.
- Normal and shiny sprite support.
- Front and back sprite support.
- Configurable settings:
  - Show or hide sprites.
  - Compact archive cards.
  - Classified-paper document theme.
  - Dark terminal document theme.
- Responsive layout for desktop, tablet, and mobile.
- Accessible labels, buttons, live status text, and semantic sections.
- No frameworks, dependencies, package manager, or build process required.

## Requirements

The project requires:

- A modern web browser.
- Python 3 if using the included local development server.
- A valid `manifest.json`.
- One or more SCP-Pokémon JSON records.

The page must be served through HTTP or HTTPS. Opening `index.html` directly with a `file://` URL may prevent JSON files from loading because of browser security restrictions.

## Project Structure

```text
project/
├── index.html
├── manifest.json
└── scp-pokemon-records/
    ├── SCP-PKMN-0001.json
    ├── SCP-PKMN-0002.json
    ├── SCP-PKMN-0003.json
    └── ...
```

Optional sprite files may also be stored locally:

```text
project/
├── sprites/
│   ├── 0001/
│   │   ├── front-normal.png
│   │   ├── back-normal.png
│   │   ├── front-shiny.png
│   │   └── back-shiny.png
│   └── ...
```

Sprite URLs can also point to remote resources.

## Manifest Format

The recommended `manifest.json` format is:

```json
{
  "records": ["SCP-PKMN-0001.json", "SCP-PKMN-0002.json", "SCP-PKMN-0003.json"]
}
```

The application resolves these files relative to:

```text
scp-pokemon-records/
```

For example:

```json
{
  "records": ["SCP-PKMN-0001.json"]
}
```

loads:

```text
scp-pokemon-records/SCP-PKMN-0001.json
```

The application also supports this alternative format:

```json
{
  "files": ["SCP-PKMN-0001.json", "SCP-PKMN-0002.json"]
}
```

## Record Format

Each record should follow the `scp-pokemon-anomaly.schema.json` structure.

A minimal compatible record looks like this:

```json
{
  "schemaVersion": "1.0.0",
  "recordId": "SCP-PKMN-0001",
  "metadata": {
    "title": "SCP-PKMN-0001: Archived Pokémon Entity",
    "author": "Foundation Data Division",
    "language": "en",
    "createdAt": "2026-08-24T12:00:00Z",
    "lastUpdatedAt": "2026-08-24T12:00:00Z"
  },
  "classification": {
    "objectClass": "safe",
    "containmentClass": "safe",
    "disruptionClass": "dark",
    "riskClass": "notice"
  },
  "pokemon": {
    "speciesName": "Pikachu",
    "regionalDexNumber": 25,
    "nationalDexNumber": 25,
    "form": "Standard",
    "biologicalSex": "unknown",
    "lifeStage": "adult",
    "primaryType": "electric",
    "secondaryType": null,
    "speciesCategory": "Mouse Pokémon",
    "heightMeters": 0.4,
    "weightKilograms": 6,
    "physicalDescription": "A standard Pikachu specimen.",
    "abilities": [
      {
        "name": "Static",
        "isHiddenAbility": false,
        "status": "standard"
      }
    ],
    "knownMoves": [
      {
        "name": "Thunder Shock",
        "type": "electric",
        "category": "special",
        "status": "standard"
      }
    ],
    "sprites": {
      "frontNormal": "sprites/0025/front-normal.png",
      "backNormal": "sprites/0025/back-normal.png",
      "frontShiny": "sprites/0025/front-shiny.png",
      "backShiny": "sprites/0025/back-shiny.png"
    }
  },
  "anomalousProperties": {
    "summary": "No additional anomaly has been recorded.",
    "properties": [
      {
        "propertyId": "AP-01",
        "name": "Baseline Pokémon Biology",
        "category": "biological",
        "description": "No additional anomalous property recorded.",
        "severity": "minimal",
        "frequency": "unknown",
        "verified": true
      }
    ],
    "threatProfile": {
      "overallThreatLevel": "negligible",
      "hazards": []
    }
  },
  "containment": {
    "containmentStatus": "contained",
    "primaryFacility": "Pokémon Data Archive",
    "containmentUnit": "Digital Record",
    "specialContainmentProcedures": "Store this record in a controlled archive.",
    "handlingProcedures": "Do not modify the source record without authorization.",
    "emergencyProcedures": "Restore the record from a verified backup."
  },
  "description": "Archived Pokémon record.",
  "status": {
    "operationalStatus": "archived",
    "lastVerifiedAt": "2026-08-24T12:00:00Z"
  }
}
```

## Sprite Properties

The viewer recognizes the following sprite properties:

```json
{
  "sprites": {
    "frontNormal": "sprites/0025/front-normal.png",
    "backNormal": "sprites/0025/back-normal.png",
    "frontShiny": "sprites/0025/front-shiny.png",
    "backShiny": "sprites/0025/back-shiny.png"
  }
}
```

Each property may contain:

- A relative local path.
- An absolute HTTPS URL.
- `null` when the sprite is unavailable.

Example using remote URLs:

```json
{
  "sprites": {
    "frontNormal": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png",
    "backNormal": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/25.png",
    "frontShiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/25.png",
    "backShiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/shiny/25.png"
  }
}
```

## Running Locally

From the project directory, run:

```bash
python -m http.server 8000
```

Open the archive at:

```text
http://localhost:8000/
```

On Windows, an alternative command is:

```powershell
py -m http.server 8000
```

To use another port:

```bash
python -m http.server 8080
```

Then visit:

```text
http://localhost:8080/
```

## Navigation

The application uses hash-based routing.

Homepage:

```text
http://localhost:8000/#/
```

Record page:

```text
http://localhost:8000/#/record/SCP-PKMN-0001
```

This works without a server-side routing configuration.

## Keyboard Shortcuts

| Key | Action                         |
| --- | ------------------------------ |
| `/` | Focus the archive search field |
| `R` | Open a random Pokémon          |
| `←` | Open the previous record       |
| `→` | Open the next record           |

Keyboard shortcuts are disabled while typing in an input, select, or textarea element.

## Favorites

Favorites are stored in the browser's local storage.

Favorite data is stored under:

```text
scp-pokemon-archive-v2
```

Favorites are browser-specific and are not written back to the JSON files.

Clearing browser site data removes the saved favorites.

## Custom Tags

Custom tags can be added directly on archive cards.

Enter tags as a comma-separated list:

```text
electric, experiment, site-19
```

Tags are normalized to lowercase and stored locally.

Example resulting tags:

```text
#electric
#experiment
#site-19
```

Tags can be searched from the main search field.

## Filtering and Sorting

The archive applies all active filters together.

For example:

```text
Search: electric
Object class: euclid
Category: Mouse Pokémon
Favorites only: enabled
Sort: Favorites first
```

Only records matching every active condition are displayed.

Previous and next navigation uses the currently filtered result set rather than the full unfiltered archive.

## Settings

The Settings dialog provides these options:

### Show sprites

Controls whether Pokémon sprites are displayed on archive cards and dossier pages.

### Compact cards

Reduces card height and hides card sprites for denser archive browsing.

### Document theme

Available themes:

- `Classified paper`
- `Dark terminal`

Settings are stored in local storage and persist between browser sessions.

## Deploying

The archive can be deployed to any static hosting provider, including:

- GitHub Pages.
- Cloudflare Pages.
- Netlify.
- Vercel static hosting.
- An Apache or Nginx web server.
- Any static file server.

Upload the complete folder while preserving the relative paths:

```text
index.html
manifest.json
scp-pokemon-records/
```

If deploying under a subdirectory, ensure the manifest and record paths remain relative to `index.html`.

## Updating Records

To add a new record:

1. Create a new JSON file in `scp-pokemon-records/`.
2. Add its filename to `manifest.json`.
3. Reload the archive.

Example:

```json
{
  "records": [
    "SCP-PKMN-0001.json",
    "SCP-PKMN-0002.json",
    "SCP-PKMN-0003.json",
    "SCP-PKMN-0025.json"
  ]
}
```

The application does not require a rebuild.

## Validation

Validate every JSON record against:

```text
scp-pokemon-anomaly.schema.json
```

Recommended validation checks:

- Every record has a unique `recordId`.
- Every record ID follows the expected format.
- Required containment fields are present.
- Required classification fields are present.
- Pokémon types use supported values.
- Sprite paths are valid.
- Dates use ISO 8601 format.
- Referenced files exist.
- `manifest.json` contains valid filenames.

The `pokemon.sprites` object should be supported by the schema:

```json
{
  "sprites": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "frontNormal": {
        "type": ["string", "null"],
        "format": "uri-reference"
      },
      "backNormal": {
        "type": ["string", "null"],
        "format": "uri-reference"
      },
      "frontShiny": {
        "type": ["string", "null"],
        "format": "uri-reference"
      },
      "backShiny": {
        "type": ["string", "null"],
        "format": "uri-reference"
      }
    }
  }
}
```

## Troubleshooting

### Records do not load

Make sure the application is being served through HTTP:

```bash
python -m http.server 8000
```

Do not open the file directly with:

```text
file:///path/to/index.html
```

### A record is missing

Check that:

- Its filename is included in `manifest.json`.
- The filename matches the actual file.
- The file is inside `scp-pokemon-records/`.
- The JSON is valid.
- The server has access to the file.

### Sprites are missing

Check that:

- The sprite URL is correct.
- The image file exists.
- The server allows the requested resource.
- The sprite property is named correctly.
- The browser console does not report a CORS error.

### Favorites or tags disappeared

Favorites and tags are stored per browser. They may be lost when:

- Browser site data is cleared.
- The hostname changes.
- The port changes.
- Private browsing mode is used.
- The browser storage quota is exceeded.

### Navigation does not show expected records

Previous and next navigation follows the active archive filters. Clear the search field and disable filters if you want to browse every record.

## Data Sources and Rights

This interface is intended for fictional, fan-created, and archival use.

Pokémon names, species, artwork, sprites, and related game data are owned by their respective rights holders. Verify the licensing terms of any external data or sprite source before publishing the archive publicly.

Do not present fictional SCP records as official Pokémon or SCP Foundation material.

## License

The interface code may be adapted for personal and non-commercial projects.

Add your own license file if the project is distributed publicly:

```text
LICENSE
```

The JSON records, artwork, sprites, Pokémon data, and SCP-inspired content may have separate ownership or licensing requirements.
