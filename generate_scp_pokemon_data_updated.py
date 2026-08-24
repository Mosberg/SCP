#!/usr/bin/env python3
"""Fetch PokéAPI locally and generate robust SCP-Pokémon dossier JSON files.

Examples:
  python generate_scp_pokemon_data_updated.py --out generated-data --limit 25
  python generate_scp_pokemon_data_updated.py --out generated-data --all --workers 4
  python generate_scp_pokemon_data_updated.py --out generated-data --all --refresh

Requires Python 3.10+ and requests.
"""
from __future__ import annotations
import argparse, hashlib, json, logging, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API = "https://pokeapi.co/api/v2"
USER_AGENT = "scp-pokemon-generator/1.1 (local archival tool)"
log = logging.getLogger("scp-generator")

TYPE_RULES = {
    "normal": (0, "safe", "low"), "fire": (2, "euclid", "moderate"),
    "water": (1, "safe", "low"), "electric": (3, "euclid", "high"),
    "grass": (1, "safe", "low"), "ice": (2, "euclid", "moderate"),
    "fighting": (2, "euclid", "moderate"), "poison": (3, "euclid", "high"),
    "ground": (3, "euclid", "high"), "flying": (1, "safe", "low"),
    "psychic": (4, "keter", "high"), "bug": (1, "safe", "low"),
    "rock": (2, "euclid", "moderate"), "ghost": (4, "keter", "high"),
    "dragon": (4, "keter", "high"), "dark": (3, "euclid", "high"),
    "steel": (2, "euclid", "moderate"), "fairy": (3, "euclid", "high")
}

HABITAT_PROCEDURES = {
    "cave": "Contain in a reinforced subterranean chamber with seismic monitoring and low-light observation.",
    "forest": "Provide a controlled indoor woodland enclosure with monitored vegetation and no unapproved exits.",
    "grassland": "Provide a secure open enclosure with reinforced perimeter fencing and remote observation.",
    "mountain": "Use a high-strength chamber with thermal, pressure, and structural monitoring.",
    "rare": "Maintain redundant containment, continuous observation, and a specialist response team.",
    "rough-terrain": "Use a reinforced habitat enclosure with terrain simulation and automated perimeter alerts.",
    "sea": "Use a sealed aquatic containment tank with pressure control, filtration, and independent life support.",
    "urban": "Contain in an insulated urban simulation chamber isolated from public infrastructure.",
    "waters-edge": "Provide a monitored shoreline or aquatic enclosure with flood-control barriers.",
    "unknown": "Use a sealed standard Pokémon containment chamber until habitat requirements are confirmed."
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resource_id(url: str | None) -> int | None:
    match = re.search(r"/(\d+)/?$", str(url or ""))
    return int(match.group(1)) if match else None


def english(entries: list[dict] | None, key: str = "name") -> str | None:
    for entry in entries or []:
        if isinstance(entry, dict) and entry.get("language", {}).get("name") == "en":
            return entry.get(key)
    return None


def clean_text(value: str | None) -> str | None:
    return re.sub(r"\s+", " ", (value or "").replace("\n", " ").replace("\f", " ")).strip() or None


def nested_name(value: Any, default: str = "unknown") -> str:
    """Safely read the name from a nullable PokéAPI named resource."""
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str) and name.strip():
            return name
    return default


def safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ApiClient:
    def __init__(self, out: Path, delay: float, timeout: float, refresh: bool):
        self.out = out
        self.delay = delay
        self.timeout = timeout
        self.refresh = refresh
        self.session = requests.Session()
        retry = Retry(
            total=6,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=16))
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    def get(self, resource: str, identifier: str | int) -> dict[str, Any]:
        safe_identifier = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(identifier))
        path = self.out / "source-data" / resource / f"{resource}-{safe_identifier}.json"
        if path.exists() and not self.refresh:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except (OSError, json.JSONDecodeError):
                log.warning("Ignoring invalid cache file: %s", path)
        if self.delay:
            time.sleep(self.delay)
        url = f"{API}/{resource}/{identifier}/"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected non-object response from {url}")
        write_json(path, data)
        return data

    def list_resource(self, resource: str) -> list[dict[str, Any]]:
        url = f"{API}/{resource}/?limit=100000&offset=0"
        cache_name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", resource)
        path = self.out / "source-data" / "_lists" / f"{cache_name}.json"
        if path.exists() and not self.refresh:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data.get("results", []) if isinstance(data, dict) else []
            except (OSError, json.JSONDecodeError):
                log.warning("Ignoring invalid list cache: %s", path)
        if self.delay:
            time.sleep(self.delay)
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        write_json(path, data)
        return data.get("results", []) if isinstance(data, dict) else []


def calculate_risk(pokemon: dict[str, Any], species: dict[str, Any]) -> dict[str, Any]:
    types = [
        entry.get("type", {}).get("name")
        for entry in pokemon.get("types", [])
        if isinstance(entry, dict) and isinstance(entry.get("type"), dict) and entry["type"].get("name")
    ]
    score = sum(TYPE_RULES.get(t, (1, "safe", "low"))[0] for t in types)
    reasons = [f"{t}-type risk profile" for t in types]
    if species.get("is_legendary"):
        score += 5
        reasons.append("legendary classification")
    if species.get("is_mythical"):
        score += 4
        reasons.append("mythical classification")
    total_stats = sum(int(x.get("base_stat", 0)) for x in pokemon.get("stats", []) if isinstance(x, dict))
    if total_stats >= 600:
        score += 4
        reasons.append("exceptional aggregate base statistics")
    elif total_stats >= 500:
        score += 2
        reasons.append("elevated aggregate base statistics")
    if len(types) > 1:
        score += 1
        reasons.append("dual-type interaction")
    if score >= 12:
        classification = ("keter", "existential", "critical")
    elif score >= 8:
        classification = ("keter", "extreme", "danger")
    elif score >= 5:
        classification = ("euclid", "high", "warning")
    elif score >= 2:
        classification = ("euclid", "moderate", "caution")
    else:
        classification = ("safe", "low", "notice")
    return {"score": score, "objectClass": classification[0], "threat": classification[1], "risk": classification[2], "reasons": reasons}


def anomaly_property(type_name: str, index: int) -> dict[str, Any]:
    descriptions = {
        "electric": "The entity produces electromagnetic discharge capable of affecting nearby equipment and biological nervous systems.",
        "psychic": "The entity demonstrates non-contact influence over perception, cognition, or information processing.",
        "ghost": "The entity can partially separate from ordinary matter and bypass conventional physical barriers.",
        "fire": "The entity produces or redirects thermal energy without a proportionate metabolic source.",
        "water": "The entity alters liquid behavior or remains functional under conditions exceeding known biology.",
        "poison": "The entity produces a biologically active substance with effects beyond known toxicology.",
        "dragon": "The entity stores and releases unusually high concentrations of bioenergetic force.",
        "fairy": "The entity produces localized emotional, perceptual, or probability-related effects."
    }
    severity = "severe" if type_name in {"psychic", "ghost", "dragon"} else "high" if type_name in {"electric", "poison", "fire"} else "moderate"
    category = "elemental" if type_name in {"fire", "water", "electric", "ice"} else "biological"
    return {"propertyId": f"AP-{index:02d}", "name": f"{type_name.title()}-Type Anomalous Expression", "category": category, "description": descriptions.get(type_name, f"The entity exhibits anomalous properties associated with its {type_name} classification."), "severity": severity, "frequency": "conditional", "verified": False}


def build_record(client: ApiClient, reference: dict[str, Any], version: str) -> dict[str, Any]:
    name = reference.get("name")
    if not name:
        raise ValueError("Pokémon reference has no name")
    pokemon = client.get("pokemon", name)
    species_ref = safe_dict(pokemon.get("species"))
    species = client.get("pokemon-species", resource_id(species_ref.get("url")) or species_ref.get("name"))
    types = [entry.get("type", {}).get("name") for entry in pokemon.get("types", []) if isinstance(entry, dict) and isinstance(entry.get("type"), dict) and entry["type"].get("name")]
    risk = calculate_risk(pokemon, species)
    habitat = nested_name(species.get("habitat"))
    now = now_iso()
    number = int(pokemon.get("id", resource_id(reference.get("url")) or 0))
    record_id = f"SCP-PKMN-{number:04d}"
    props = [anomaly_property(t, i) for i, t in enumerate(dict.fromkeys(types), 1)] or [anomaly_property("unknown", 1)]
    procedure = HABITAT_PROCEDURES.get(habitat, HABITAT_PROCEDURES["unknown"])
    if risk["score"] >= 8:
        procedure += " Maintain redundant barriers, continuous observation, and an authorized specialist response team."
    sprites = safe_dict(pokemon.get("sprites"))
    other = safe_dict(sprites.get("other"))
    artwork = safe_dict(other.get("official-artwork"))
    moves = [{"name": entry["move"]["name"], "type": "unknown", "category": "unknown", "status": "unverified"} for entry in pokemon.get("moves", []) if isinstance(entry, dict) and isinstance(entry.get("move"), dict) and entry["move"].get("name")]
    abilities = [{"name": entry["ability"]["name"], "isHiddenAbility": bool(entry.get("is_hidden", False)), "status": "standard"} for entry in pokemon.get("abilities", []) if isinstance(entry, dict) and isinstance(entry.get("ability"), dict) and entry["ability"].get("name")]
    genus = english(species.get("genera"), "genus")
    flavor = clean_text(english(species.get("flavor_text_entries"), "flavor_text")) or f"Imported PokéAPI record for {name}."
    return {
        "schemaVersion": "1.0.0", "recordId": record_id,
        "generation": {"generator": "scp-pokemon-anomaly-generator", "generatorVersion": version, "seed": hashlib.sha256(f"{record_id}:{version}".encode()).hexdigest()[:16], "source": API, "generatedAt": now},
        "metadata": {"title": f"{record_id}: {(english(species.get('names')) or name).title()}", "author": "Automated Foundation Data Division", "language": "en", "createdAt": now, "lastUpdatedAt": now, "publicationStatus": "draft", "canon": "Generated SCP-Pokémon Fan Continuity"},
        "classification": {"objectClass": risk["objectClass"], "containmentClass": risk["objectClass"], "disruptionClass": "keneq" if risk["score"] >= 5 else "dark", "riskClass": risk["risk"], "classificationRationale": "; ".join(risk["reasons"])},
        "pokemon": {"speciesName": english(species.get("names")) or name, "regionalDexNumber": number, "nationalDexNumber": number, "form": "Standard" if pokemon.get("is_default", True) else name, "biologicalSex": "unknown", "lifeStage": "adult", "primaryType": types[0] if types else "unknown", "secondaryType": types[1] if len(types) > 1 else None, "speciesCategory": genus, "heightMeters": pokemon.get("height", 0) / 10 or None, "weightKilograms": pokemon.get("weight", 0) / 10 or None, "physicalDescription": flavor, "abilities": abilities, "knownMoves": moves, "sprites": {"frontNormal": sprites.get("front_default"), "backNormal": sprites.get("back_default"), "frontShiny": sprites.get("front_shiny"), "backShiny": sprites.get("back_shiny"), "frontOfficialArtwork": artwork.get("front_default"), "frontShinyOfficialArtwork": artwork.get("front_shiny")}},
        "anomalousProperties": {"summary": f"Automatically generated anomaly profile for a {'legendary' if species.get('is_legendary') else 'mythical' if species.get('is_mythical') else 'standard'} Pokémon associated with the {', '.join(types) or 'unknown'} type profile.", "originStatus": "theorized", "properties": props, "threatProfile": {"overallThreatLevel": risk["threat"], "hazards": [], "riskSummary": f"Risk score {risk['score']}: {'; '.join(risk['reasons'])}"}},
        "containment": {"containmentStatus": "contained", "primaryFacility": "Pokémon Anomaly Archive", "containmentUnit": "High-Risk Habitat Simulation Chamber" if risk["score"] >= 5 else "Standard Habitat Simulation Chamber", "specialContainmentProcedures": procedure, "handlingProcedures": "Interaction is restricted to authorized Pokémon handlers and approved research personnel.", "environmentalRequirements": {"habitatType": habitat}, "emergencyProcedures": "Activate site lockdown, isolate the habitat, and deploy the entity-specific recovery team."},
        "description": flavor, "status": {"operationalStatus": "archived", "lastVerifiedAt": now}
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("generated-data"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--all", action="store_true", help="Generate every default Pokémon up to the current National Dex range.")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--generator-version", default="1.1.0")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1: parser.error("--limit must be positive")
    if not 1 <= args.workers <= 12: parser.error("--workers must be between 1 and 12")
    if args.delay < 0 or args.timeout <= 0: parser.error("--delay must be non-negative and --timeout must be positive")
    return args


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    client = ApiClient(args.out, args.delay, args.timeout, args.refresh)
    references = client.list_resource("pokemon")
    references = [x for x in references if (resource_id(x.get("url")) or 0) <= 1025]
    if args.limit is not None:
        references = references[:args.limit]
    output = args.out / "scp-pokemon-records"
    completed: list[str] = []
    failures: list[dict[str, str]] = []

    def process(reference: dict[str, Any]) -> str:
        record = build_record(client, reference, args.generator_version)
        write_json(output / f"{record['recordId']}.json", record)
        return record["recordId"]

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process, ref): ref.get("name", "unknown") for ref in references}
        for future in as_completed(futures):
            source_name = futures[future]
            try:
                record_id = future.result()
                completed.append(record_id)
                log.info("Generated %s", record_id)
            except Exception as error:
                message = f"{type(error).__name__}: {error}"
                failures.append({"name": source_name, "error": message})
                log.error("Failed %s: %s", source_name, message)

    completed.sort()
    write_json(args.out / "manifest.json", {"generatedAt": now_iso(), "source": API, "records": [f"{record_id}.json" for record_id in completed]})
    write_json(args.out / "generation-report.json", {"generatedAt": now_iso(), "requested": len(references), "completed": len(completed), "failed": len(failures), "failures": failures, "generatorVersion": args.generator_version})
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
