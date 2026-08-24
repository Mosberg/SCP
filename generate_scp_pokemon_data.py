#!/usr/bin/env python3
"""Fetch PokéAPI locally and generate SCP-Pokémon dossier JSON files.

Examples:
  python generate_scp_pokemon_data.py --out data --limit 25
  python generate_scp_pokemon_data.py --out data --all --workers 6
  python generate_scp_pokemon_data.py --out data --refresh

Requires: Python 3.10+, requests
"""
from __future__ import annotations
import argparse, hashlib, json, logging, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API = "https://pokeapi.co/api/v2"
UA = "scp-pokemon-generator/1.0 (local archival tool)"
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
    "steel": (2, "euclid", "moderate"), "fairy": (3, "euclid", "high"),
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
    "unknown": "Use a sealed standard Pokémon containment chamber until habitat requirements are confirmed.",
}

def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def rid(url: str | None) -> int | None:
    m = re.search(r"/(\d+)/?$", str(url or "")); return int(m.group(1)) if m else None

def en(entries: list[dict], key: str = "name") -> str | None:
    for x in entries or []:
        if x.get("language", {}).get("name") == "en":
            return x.get(key)
    return None

def names(entries: list[dict]) -> str | None: return en(entries, "name")
def flavor(entries: list[dict]) -> str | None: return en(entries, "flavor_text")

def clean_text(value: str | None) -> str | None:
    return re.sub(r"\s+", " ", (value or "").replace("\n", " ").replace("\f", " ")).strip() or None

def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

class Client:
    def __init__(self, out: Path, delay: float, timeout: float, refresh: bool):
        self.out, self.delay, self.timeout, self.refresh = out, delay, timeout, refresh
        self.session = requests.Session()
        retry = Retry(total=6, backoff_factor=1, status_forcelist=(429,500,502,503,504), allowed_methods=frozenset(["GET"]), respect_retry_after_header=True)
        self.session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=16))
        self.session.headers.update({"User-Agent": UA, "Accept": "application/json"})

    def get(self, resource: str, identifier: str | int) -> dict:
        key = f"{resource}-{identifier}".lower().replace("/", "-")
        path = self.out / "source-data" / resource / f"{key}.json"
        if path.exists() and not self.refresh:
            return json.loads(path.read_text(encoding="utf-8"))
        if self.delay: time.sleep(self.delay)
        url = f"{API}/{resource}/{identifier}/"
        response = self.session.get(url, timeout=self.timeout); response.raise_for_status()
        data = response.json(); write(path, data); return data

    def list(self, resource: str) -> list[dict]:
        return self.get_list_url(f"{API}/{resource}/?limit=100000&offset=0").get("results", [])

    def get_list_url(self, url: str) -> dict:
        path = self.out / "source-data" / "_lists" / (re.sub(r"[^a-z0-9]+", "_", url.lower()) + ".json")
        if path.exists() and not self.refresh: return json.loads(path.read_text(encoding="utf-8"))
        if self.delay: time.sleep(self.delay)
        r = self.session.get(url, timeout=self.timeout); r.raise_for_status(); data = r.json(); write(path, data); return data

def risk(p: dict, species: dict) -> dict:
    types = [x["type"]["name"] for x in p.get("types", [])]
    score = sum(TYPE_RULES.get(t, (1,"safe","low"))[0] for t in types)
    reasons = [f"{t}-type risk profile" for t in types]
    legendary, mythical = species.get("is_legendary", False), species.get("is_mythical", False)
    if legendary: score += 5; reasons.append("legendary classification")
    if mythical: score += 4; reasons.append("mythical classification")
    total = sum(x.get("base_stat", 0) for x in p.get("stats", []))
    if total >= 600: score += 4; reasons.append("exceptional aggregate base statistics")
    elif total >= 500: score += 2; reasons.append("elevated aggregate base statistics")
    if len(types) == 2: score += 1; reasons.append("dual-type interaction")
    if score >= 12: return {"score":score,"objectClass":"keter","threat":"existential","risk":"critical","reasons":reasons}
    if score >= 8: return {"score":score,"objectClass":"keter","threat":"extreme","risk":"danger","reasons":reasons}
    if score >= 5: return {"score":score,"objectClass":"euclid","threat":"high","risk":"warning","reasons":reasons}
    if score >= 2: return {"score":score,"objectClass":"euclid","threat":"moderate","risk":"caution","reasons":reasons}
    return {"score":score,"objectClass":"safe","threat":"low","risk":"notice","reasons":reasons}

def property_for(t: str, index: int) -> dict:
    descriptions = {
        "electric":"The entity produces electromagnetic discharge capable of affecting nearby equipment and biological nervous systems.",
        "psychic":"The entity demonstrates non-contact influence over perception, cognition, or information processing.",
        "ghost":"The entity can partially separate from ordinary matter and bypass conventional physical barriers.",
        "fire":"The entity produces or redirects thermal energy without a proportionate metabolic source.",
        "water":"The entity alters liquid behavior or remains functional under conditions that exceed known biology.",
        "poison":"The entity produces a biologically active substance with effects beyond known toxicology.",
        "dragon":"The entity stores and releases unusually high concentrations of bioenergetic force.",
        "fairy":"The entity produces localized emotional, perceptual, or probability-related effects.",
    }
    return {"propertyId":f"AP-{index:02d}","name":f"{t.title()}-Type Anomalous Expression","category":"elemental" if t in {"fire","water","electric","ice"} else "biological","description":descriptions.get(t,f"The entity exhibits anomalous properties associated with its {t} classification."),"severity":"severe" if t in {"psychic","ghost","dragon"} else "high" if t in {"electric","poison","fire"} else "moderate","frequency":"conditional","verified":False}

def build(client: Client, ref: dict, version: str) -> dict:
    p = client.get("pokemon", ref["name"]); species = client.get("pokemon-species", rid(p["species"]["url"]) or p["species"]["name"])
    types = [x["type"]["name"] for x in p.get("types", [])]; r = risk(p, species); habitat = species.get("habitat", {}).get("name", "unknown"); now=iso_now(); number=p["id"]
    props=[property_for(t,i) for i,t in enumerate(dict.fromkeys(types),1)] or [property_for("unknown",1)]
    containment = HABITAT_PROCEDURES.get(habitat, HABITAT_PROCEDURES["unknown"])
    if r["score"] >= 8: containment += " Maintain redundant barriers, continuous observation, and an authorized specialist response team."
    sprites=p.get("sprites",{}); record_id=f"SCP-PKMN-{number:04d}"
    moves=[{"name":x["move"]["name"],"type":"unknown","category":"unknown","status":"unverified"} for x in p.get("moves",[])]
    abilities=[{"name":x["ability"]["name"],"isHiddenAbility":x.get("is_hidden",False),"status":"standard"} for x in p.get("abilities",[])]
    return {"schemaVersion":"1.0.0","recordId":record_id,"generation":{"generator":"scp-pokemon-anomaly-generator","generatorVersion":version,"seed":hashlib.sha256(f"{record_id}:{version}".encode()).hexdigest()[:16],"source":"PokéAPI","generatedAt":now},"metadata":{"title":f"{record_id}: {(names(species.get('names',[])) or p['name']).title()}","author":"Automated Foundation Data Division","language":"en","createdAt":now,"lastUpdatedAt":now,"publicationStatus":"draft","canon":"Generated SCP-Pokémon Fan Continuity"},"classification":{"objectClass":r["objectClass"],"containmentClass":r["objectClass"],"disruptionClass":"keneq" if r["score"]>=5 else "dark","riskClass":r["risk"],"classificationRationale":"; ".join(r["reasons"])},"pokemon":{"speciesName":names(species.get("names",[])) or p["name"],"regionalDexNumber":number,"nationalDexNumber":number,"form":"Standard" if p.get("is_default",True) else p["name"],"biologicalSex":"unknown","lifeStage":"adult","primaryType":types[0] if types else "unknown","secondaryType":types[1] if len(types)>1 else None,"speciesCategory":en(species.get("genera",[]),"genus"),"heightMeters":p.get("height",0)/10 or None,"weightKilograms":p.get("weight",0)/10 or None,"physicalDescription":clean_text(flavor(species.get("flavor_text_entries",[]))) or f"Imported {p['name']} specimen.","abilities":abilities,"knownMoves":moves,"sprites":{"frontNormal":sprites.get("front_default"),"backNormal":sprites.get("back_default"),"frontShiny":sprites.get("front_shiny"),"backShiny":sprites.get("back_shiny"),"frontOfficialArtwork":sprites.get("other",{}).get("official-artwork",{}).get("front_default"),"frontShinyOfficialArtwork":sprites.get("other",{}).get("official-artwork",{}).get("front_shiny")}},"anomalousProperties":{"summary":f"Automatically generated anomaly profile for a {'legendary' if species.get('is_legendary') else 'mythical' if species.get('is_mythical') else 'standard'} Pokémon associated with the {', '.join(types) or 'unknown'} type profile.","originStatus":"theorized","properties":props,"threatProfile":{"overallThreatLevel":r["threat"],"hazards":[],"riskSummary":f"Risk score {r['score']}: {'; '.join(r['reasons'])}"}},"containment":{"containmentStatus":"contained","primaryFacility":"Pokémon Anomaly Archive","containmentUnit":"High-Risk Habitat Simulation Chamber" if r["score"]>=5 else "Standard Habitat Simulation Chamber","specialContainmentProcedures":containment,"handlingProcedures":"Interaction is restricted to authorized Pokémon handlers and approved research personnel.","environmentalRequirements":{"habitatType":habitat},"emergencyProcedures":"Activate site lockdown, isolate the habitat, and deploy the entity-specific recovery team."},"description":clean_text(flavor(species.get("flavor_text_entries",[]))) or f"Automated dossier for {p['name']}.","status":{"operationalStatus":"archived","lastVerifiedAt":now}}

def args():
    a=argparse.ArgumentParser();a.add_argument("--out",type=Path,default=Path("generated-data"));a.add_argument("--limit",type=int);a.add_argument("--all",action="store_true");a.add_argument("--workers",type=int,default=4);a.add_argument("--delay",type=float,default=.1);a.add_argument("--timeout",type=float,default=30);a.add_argument("--refresh",action="store_true");a.add_argument("--generator-version",default="1.0.0");return a.parse_args()

def main():
    logging.basicConfig(level=logging.INFO,format="%(levelname)s: %(message)s"); a=args(); a.out.mkdir(parents=True,exist_ok=True); client=Client(a.out,a.delay,a.timeout,a.refresh)
    refs=client.list("pokemon"); refs=[x for x in refs if (rid(x["url"]) or 0)<=1025]
    if a.limit is not None: refs=refs[:a.limit]
    out=a.out/"scp-pokemon-records"; results=[]
    def one(ref):
        record=build(client,ref,a.generator_version); write(out/f"{record['recordId']}.json",record); return record["recordId"]
    with ThreadPoolExecutor(max_workers=max(1,min(a.workers,12))) as pool:
        futures=[pool.submit(one,x) for x in refs]
        for f in as_completed(futures):
            try: results.append(f.result())
            except Exception as e: log.error("Failed record: %s",e)
    results.sort(); write(a.out/"manifest.json",{"generatedAt":iso_now(),"source":"https://pokeapi.co/api/v2","records":[f"{x}.json" for x in results]}); write(a.out/"generation-report.json",{"requested":len(refs),"completed":len(results),"failed":len(refs)-len(results),"generatorVersion":a.generator_version}); return 0 if len(results)==len(refs) else 1
if __name__=="__main__": sys.exit(main())
