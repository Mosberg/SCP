#!/usr/bin/env python3
"""Build a Pokémon dataset from PokéAPI, plus SCP-Pokémon anomaly records.

Usage:
    python build_scp_pokemon_dataset.py --out data --limit 1025
    python build_scp_pokemon_dataset.py --out data --all

The generated scp-pokemon-records/*.json files are valid instances of
scp-pokemon-anomaly.schema.json for ordinary, non-anomalous Pokémon. Extend
anomalousProperties and containment when authoring an anomaly dossier.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_ROOT = "https://pokeapi.co/api/v2"
SPRITE_ROOT = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites"
SCHEMA_VERSION = "1.0.0"
USER_AGENT = "scp-pokemon-dataset-builder/1.0 (PokéAPI consumer; local caching enabled)"
LOG = logging.getLogger("scp-pokemon")


@dataclass(frozen=True)
class Config:
    out: Path
    workers: int
    timeout: float
    delay: float
    limit: int | None
    overwrite: bool


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resource_id(url: str | None) -> int | None:
    if not url:
        return None
    match = re.search(r"/(\d+)/?$", urlparse(url).path)
    return int(match.group(1)) if match else None


def localized(entries: list[dict[str, Any]], language: str = "en") -> str | None:
    for entry in entries or []:
        if entry.get("language", {}).get("name") == language:
            return entry.get("flavor_text") or entry.get("effect") or entry.get("name")
    return None


def names(entries: list[dict[str, Any]], language: str = "en") -> str | None:
    for entry in entries or []:
        if entry.get("language", {}).get("name") == language:
            return entry.get("name")
    return None


class ApiClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        retry = Retry(
            total=6,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=config.workers))
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    def get_json(self, url: str) -> dict[str, Any]:
        cache = self.config.out / "cache" / (slug(url.rstrip("/").split("/")[-2] + "-" + url.rstrip("/").split("/")[-1]) + ".json")
        cache.parent.mkdir(parents=True, exist_ok=True)
        if cache.exists() and not self.config.overwrite:
            return json.loads(cache.read_text(encoding="utf-8"))
        if self.config.delay:
            time.sleep(self.config.delay)
        response = self.session.get(url, timeout=self.config.timeout)
        response.raise_for_status()
        data = response.json()
        cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def get(self, resource: str, identifier: str | int) -> dict[str, Any]:
        return self.get_json(f"{API_ROOT}/{resource}/{identifier}/")

    def list_all(self, resource: str) -> list[dict[str, Any]]:
        data = self.get_json(f"{API_ROOT}/{resource}/?limit=100000&offset=0")
        return data.get("results", [])


def collect_resources(client: ApiClient, config: Config) -> dict[str, Any]:
    """Collect complete related resource tables once; records reference these tables by ID."""
    resource_names = [
        "ability", "berry", "berry-firmness", "berry-flavor", "characteristic",
        "contest-effect", "contest-type", "egg-group", "encounter-condition",
        "encounter-condition-value", "encounter-method", "evolution-chain",
        "evolution-trigger", "generation", "gender", "growth-rate", "item",
        "item-attribute", "item-category", "item-fling-effect", "item-pocket",
        "location", "location-area", "machine", "move", "move-ailment",
        "move-battle-style", "move-category", "move-damage-class", "move-learn-method",
        "move-target", "nature", "pal-park-area", "pokeathlon-stat", "pokedex",
        "pokemon-color", "pokemon-form", "pokemon-habitat", "pokemon-shape",
        "pokemon-species", "region", "stat", "super-contest-effect", "type",
        "version", "version-group",
    ]
    catalog: dict[str, Any] = {}
    for resource in resource_names:
        LOG.info("Listing %s", resource)
        catalog[resource] = client.list_all(resource)
    write_json(config.out / "catalog" / "resource-index.json", catalog)
    return catalog


def sprite_urls(pokemon: dict[str, Any]) -> dict[str, str | None]:
    s = pokemon.get("sprites", {})
    versions = s.get("versions", {})
    # Prefer the API's canonical generation sprite when available; fall back to
    # the stable GitHub sprite paths. Missing back sprites are explicitly null.
    return {
        "frontNormal": s.get("front_default"),
        "backNormal": s.get("back_default"),
        "frontShiny": s.get("front_shiny"),
        "backShiny": s.get("back_shiny"),
        "frontOfficialArtwork": s.get("other", {}).get("official-artwork", {}).get("front_default"),
        "frontShinyOfficialArtwork": s.get("other", {}).get("official-artwork", {}).get("front_shiny"),
        "frontFallback": f"{SPRITE_ROOT}/pokemon/{pokemon['id']}.png",
        "backFallback": f"{SPRITE_ROOT}/pokemon/back/{pokemon['id']}.png",
        "frontShinyFallback": f"{SPRITE_ROOT}/pokemon/shiny/{pokemon['id']}.png",
        "backShinyFallback": f"{SPRITE_ROOT}/pokemon/back/shiny/{pokemon['id']}.png",
    }


def build_record(client: ApiClient, pokemon: dict[str, Any], config: Config) -> dict[str, Any]:
    species = client.get("pokemon-species", resource_id(pokemon["species"]["url"]) or pokemon["species"]["name"])
    types = [x["type"]["name"] for x in pokemon.get("types", [])]
    primary = types[0] if types else "unknown"
    secondary = types[1] if len(types) > 1 else None
    record_id = f"SCP-PKMN-{pokemon['id']:04d}"
    timestamp = now_iso()
    moves = []
    for entry in pokemon.get("moves", []):
        detail = entry["move"]
        moves.append({"name": detail["name"], "type": "unknown", "category": "unknown", "status": "unverified"})
    abilities = [{"name": x["ability"]["name"], "isHiddenAbility": x.get("is_hidden", False), "status": "standard"} for x in pokemon.get("abilities", [])]
    stats = {x["stat"]["name"].replace("special-attack", "specialAttack").replace("special-defense", "specialDefense"): x["base_stat"] for x in pokemon.get("stats", [])}
    return {
        "schemaVersion": SCHEMA_VERSION,
        "recordId": record_id,
        "metadata": {"title": f"{record_id}: {pokemon['name'].replace('-', ' ').title()}", "author": "PokéAPI Importer", "language": "en", "createdAt": timestamp, "lastUpdatedAt": timestamp, "publicationStatus": "draft"},
        "classification": {"objectClass": "safe", "containmentClass": "safe", "disruptionClass": "dark", "riskClass": "notice"},
        "pokemon": {
            "speciesName": names(species.get("names", [])) or species["name"],
            "scientificDesignation": None,
            "regionalDexNumber": pokemon["id"],
            "nationalDexNumber": pokemon["id"],
            "speciesCategory": localized(species.get("genera", [])) or None,
            "form": "Standard" if pokemon.get("is_default", True) else pokemon["name"],
            "biologicalSex": "unknown",
            "lifeStage": "adult",
            "shinyStatus": "standard",
            "heightMeters": pokemon.get("height", 0) / 10 or None,
            "weightKilograms": pokemon.get("weight", 0) / 10 or None,
            "physicalDescription": localized(species.get("flavor_text_entries", [])) or f"Pokémon species: {species['name']}.",
            "primaryType": primary,
            "secondaryType": secondary,
            "knownMoves": moves,
            "abilities": abilities,
            "baseStats": stats,
            "sprites": sprite_urls(pokemon)
        },
        "anomalousProperties": {"summary": "No anomaly has been authored for this imported Pokémon record.", "properties": [{"propertyId": "AP-01", "name": "Baseline Pokémon Biology", "category": "biological", "description": "No additional anomalous property recorded.", "severity": "minimal", "frequency": "unknown", "verified": True}], "threatProfile": {"overallThreatLevel": "negligible", "hazards": []}},
        "containment": {"containmentStatus": "contained", "primaryFacility": "Pokémon Data Archive", "containmentUnit": "Digital Record", "specialContainmentProcedures": "Store this record in a controlled local archive.", "handlingProcedures": "Do not treat canonical data as an anomaly report without review.", "emergencyProcedures": "Restore the record from the cached source response."},
        "description": localized(species.get("flavor_text_entries", [])) or f"Imported PokéAPI record for {species['name']}.",
        "status": {"operationalStatus": "archived", "lastVerifiedAt": timestamp}
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def download(url: str, destination: Path, client: ApiClient) -> bool:
    if destination.exists() and not client.config.overwrite:
        return True
    try:
        if client.config.delay:
            time.sleep(client.config.delay)
        response = client.session.get(url, timeout=client.config.timeout)
        if response.status_code == 404:
            return False
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return True
    except requests.RequestException as exc:
        LOG.warning("Sprite failed %s: %s", url, exc)
        return False


def process_one(client: ApiClient, pokemon_ref: dict[str, str], config: Config) -> str:
    pokemon = client.get("pokemon", pokemon_ref["name"])
    record = build_record(client, pokemon, config)
    out = config.out / "scp-pokemon-records" / f"{record['recordId']}.json"
    write_json(out, record)
    urls = sprite_urls(pokemon)
    for key, url in urls.items():
        if url and key.endswith(("Normal", "Shiny")):
            download(url, config.out / "sprites" / f"{pokemon['id']:04d}" / f"{slug(key)}.png", client)
    return record["recordId"]


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("pokemon-data"))
    parser.add_argument("--limit", type=int, default=None, help="Only import the first N default Pokémon.")
    parser.add_argument("--all", action="store_true", help="Import every Pokémon form returned by the API.")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--delay", type=float, default=0.05, help="Delay before uncached requests, in seconds.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 12 or args.timeout <= 0 or args.delay < 0:
        parser.error("workers must be 1..12, timeout must be positive, and delay cannot be negative")
    return Config(args.out, args.workers, args.timeout, args.delay, args.limit, args.overwrite)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = parse_args()
    client = ApiClient(config)
    refs = client.list_all("pokemon")
    if not config.out.joinpath("catalog", "resource-index.json").exists() or config.overwrite:
        collect_resources(client, config)
    refs = [x for x in refs if config.out.joinpath("cache", f"pokemon-{x['name']}.json").exists() or True]
    if not config.__dict__.get("all", False):
        refs = [x for x in refs if resource_id(x["url"]) and resource_id(x["url"]) <= 1025]
    if config.limit is not None:
        refs = refs[:config.limit]
    completed = 0
    with ThreadPoolExecutor(max_workers=config.workers) as pool:
        futures = [pool.submit(process_one, client, ref, config) for ref in refs]
        for future in as_completed(futures):
            try:
                LOG.info("Built %s", future.result())
                completed += 1
            except Exception as exc:
                LOG.error("Record failed: %s", exc)
    write_json(config.out / "manifest.json", {"generatedAt": now_iso(), "source": API_ROOT, "recordsCompleted": completed, "recordsRequested": len(refs), "spriteDirectory": "sprites", "schema": "scp-pokemon-anomaly.schema.json"})
    return 0 if completed == len(refs) else 1


if __name__ == "__main__":
    sys.exit(main())
