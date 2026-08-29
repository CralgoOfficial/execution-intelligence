import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".publication" / "zenodo-state.json"
FINAL_PDF = ROOT / "dist" / "Execution_Intelligence_Judgement_Carried_into_Execution_v1.0.pdf"
TITLE = "Execution Intelligence: Judgement Carried into Execution"
VERSION = "1.0"
ZENODO_API = "https://zenodo.org/api"
REPO_URL = "https://github.com/CralgoOfficial/execution-intelligence"
CONCEPT_URL = "https://cralgo.com/execution-intelligence"
RESEARCH_URL = "https://cralgo.com/research"

ABSTRACT = (
    "Execution Intelligence is a Cralgo concept concerned with how informed judgement is carried "
    "from organisational intent into execution without losing the context, priorities and reasoning "
    "that made the original direction meaningful. The paper proposes Context -> Judgement -> "
    "Priorities -> Structure -> Governance -> Execution -> Learning as an integrative conceptual "
    "lens rather than a rigid methodology. It introduces judgement continuity as the central object "
    "of attention and uses execution drift as descriptive shorthand for the gradual separation of "
    "action from the judgement and intent that originally gave it meaning. The concept is situated "
    "alongside established work on sensemaking, deliberate and emergent strategy, organisational "
    "learning, organisational routines and dynamic capabilities. The phrase execution intelligence "
    "predates this paper and is not claimed as newly coined by Cralgo. The proposed contribution is "
    "the specific formulation centred on judgement continuity and a research agenda for testing, "
    "refining or rejecting that formulation. It is presented as a conceptual contribution, not an "
    "industry standard or empirically validated theory."
)

KEYWORDS = [
    "Execution Intelligence",
    "judgement continuity",
    "execution drift",
    "organisational execution",
    "governance",
    "organisational capability",
    "technology governance",
    "organisational learning",
    "strategy execution",
    "sensemaking",
]


def token() -> str:
    value = os.environ.get("ZENODO_TOKEN", "").strip()
    if not value:
        raise RuntimeError("ZENODO_TOKEN is missing. Add it as a GitHub Actions repository secret.")
    return value


def headers(json_content=False):
    h = {"Authorization": f"Bearer {token()}"}
    if json_content:
        h["Content-Type"] = "application/json"
    return h


def check(response, expected):
    if response.status_code not in expected:
        try:
            body = response.json()
        except Exception:
            body = response.text
        raise RuntimeError(f"Zenodo API error {response.status_code}: {body}")
    return response


def read_state():
    if not STATE_PATH.exists():
        return None
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def write_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def metadata(publication_date):
    description = (
        f"<p>{ABSTRACT}</p>"
        f"<p><strong>Cralgo Research:</strong> <a href=\"{RESEARCH_URL}\">{RESEARCH_URL}</a><br>"
        f"<strong>Concept page:</strong> <a href=\"{CONCEPT_URL}\">{CONCEPT_URL}</a><br>"
        f"<strong>Public source repository:</strong> <a href=\"{REPO_URL}\">{REPO_URL}</a></p>"
        "<p><em>A Cralgo Concept Paper.</em></p>"
    )
    return {
        "upload_type": "publication",
        "publication_type": "other",
        "publication_date": publication_date,
        "title": TITLE,
        "creators": [{"name": "Kumar, Anil Kabir", "affiliation": "Cralgo"}],
        "description": description,
        "access_right": "open",
        "license": "cc-by-nc-nd-4.0",
        "keywords": KEYWORDS,
        "version": VERSION,
        "language": "eng",
        "notes": "A Cralgo Concept Paper. The paper is a conceptual contribution and research agenda, not an industry standard or empirically validated theory.",
    }


def create_or_reuse_deposit():
    state = read_state()
    if state and state.get("deposit_id"):
        r = requests.get(f"{ZENODO_API}/deposit/depositions/{state['deposit_id']}", headers=headers())
        check(r, {200})
        dep = r.json()
        doi = dep.get("metadata", {}).get("prereserve_doi", {}).get("doi") or state.get("doi")
        if not doi:
            raise RuntimeError("Existing Zenodo draft does not expose a reserved DOI.")
        state["doi"] = doi
        state["bucket_url"] = dep["links"]["bucket"]
        state["draft_url"] = dep["links"].get("html") or dep["links"].get("latest_draft_html")
        write_state(state)
        return dep, state

    publication_date = datetime.now(timezone.utc).date().isoformat()
    payload = {"metadata": metadata(publication_date)}
    r = requests.post(f"{ZENODO_API}/deposit/depositions", headers=headers(True), json=payload)
    check(r, {201})
    dep = r.json()
    doi = dep.get("metadata", {}).get("prereserve_doi", {}).get("doi")
    if not doi:
        raise RuntimeError("Zenodo created a draft but did not return a pre-reserved DOI.")
    state = {
        "title": TITLE,
        "version": VERSION,
        "status": "doi_reserved",
        "deposit_id": dep["id"],
        "record_id": dep.get("record_id"),
        "doi": doi,
        "bucket_url": dep["links"]["bucket"],
        "draft_url": dep["links"].get("html") or dep["links"].get("latest_draft_html"),
        "publication_date": publication_date,
    }
    write_state(state)
    return dep, state


def update_text_files(doi, publication_date, published=False, zenodo_url=None):
    paper_path = ROOT / "paper.md"
    paper = paper_path.read_text(encoding="utf-8")
    paper = paper.replace("**DOI:** Pending reservation", f"**DOI:** {doi}")
    paper = paper.replace("DOI: Pending reservation", f"DOI: {doi}")
    paper_path.write_text(paper, encoding="utf-8")

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = readme.replace("> **Publication status:** Pre-publication / DOI pending", "> **Publication status:** Published" if published else "> **Publication status:** DOI reserved / publishing")
    readme = readme.replace("The Zenodo DOI will be reserved before the final PDF is published. Once reserved, the DOI will be written back into this repository, the final PDF and citation metadata.", f"**DOI:** https://doi.org/{doi}")
    readme = readme.replace("Until that happens, this repository should be treated as the public pre-publication home of the concept, not the DOI-backed final record.", "The DOI-backed Zenodo record is the authoritative persistent publication record." if published else "The DOI has been reserved and will become active when the Zenodo record is published.")
    if zenodo_url and "Zenodo record:" not in readme:
        readme = readme.replace(f"**DOI:** https://doi.org/{doi}", f"**DOI:** https://doi.org/{doi}  \n**Zenodo record:** {zenodo_url}")
    readme_path.write_text(readme, encoding="utf-8")

    cff_path = ROOT / "CITATION.cff"
    cff = cff_path.read_text(encoding="utf-8")
    cff = re.sub(r'message: ".*?"', 'message: "If you reference this work, please cite the DOI-backed v1.0 record."', cff, count=1)
    if not re.search(r"(?m)^doi:", cff):
        cff = cff.replace('version: "1.0"', f'version: "1.0"\ndate-released: "{publication_date}"\ndoi: "{doi}"')
    else:
        cff = re.sub(r'(?m)^doi:.*$', f'doi: "{doi}"', cff)
    cff = re.sub(r'(?ms)^notes: >-\n(?:  .*\n?)+', 'notes: >-\n  DOI-backed v1.0 publication record.\n', cff)
    cff_path.write_text(cff, encoding="utf-8")

    publication_path = ROOT / "PUBLICATION.md"
    if publication_path.exists():
        text = publication_path.read_text(encoding="utf-8")
        text = text.replace("DOI pending", f"DOI {doi}")
        text = text.replace("DOI: Pending reservation", f"DOI: {doi}")
        if published:
            text += f"\n\n## Published record\n\n- DOI: https://doi.org/{doi}\n- Zenodo: {zenodo_url or f'https://doi.org/{doi}'}\n- GitHub release: https://github.com/CralgoOfficial/execution-intelligence/releases/tag/v1.0\n"
        publication_path.write_text(text, encoding="utf-8")


def build_pdf(doi, publication_date):
    month_year = datetime.fromisoformat(publication_date).strftime("%B %Y")
    env = os.environ.copy()
    env["PUBLICATION_DOI"] = doi
    env["PUBLICATION_DATE"] = month_year
    env["EI_SOURCE"] = str(ROOT / "paper.md")
    env["EI_OUTPUT"] = str(FINAL_PDF)
    subprocess.run([sys.executable, str(ROOT / "automation" / "build_pdf.py")], env=env, check=True)
    if not FINAL_PDF.exists():
        raise RuntimeError("Final PDF was not generated.")


def upload_pdf(state):
    bucket = state["bucket_url"].rstrip("/")
    target = f"{bucket}/{FINAL_PDF.name}"
    with FINAL_PDF.open("rb") as fh:
        r = requests.put(target, headers=headers(), data=fh)
    check(r, {200, 201})


def update_deposit_metadata(state):
    payload = {"metadata": metadata(state["publication_date"])}
    r = requests.put(f"{ZENODO_API}/deposit/depositions/{state['deposit_id']}", headers=headers(True), json=payload)
    check(r, {200})
    return r.json()


def prepare():
    dep, state = create_or_reuse_deposit()
    if dep.get("submitted"):
        raise RuntimeError("The Zenodo record is already published; refusing to rebuild a published v1.0 deposit.")

    update_text_files(state["doi"], state["publication_date"], published=False)
    build_pdf(state["doi"], state["publication_date"])
    update_deposit_metadata(state)
    upload_pdf(state)
    state["status"] = "ready_to_publish"
    state["final_pdf"] = str(FINAL_PDF.relative_to(ROOT))
    write_state(state)
    print(json.dumps(state, indent=2))


def publish():
    state = read_state()
    if not state or not state.get("deposit_id"):
        raise RuntimeError("No Zenodo state exists. Run prepare first.")

    r = requests.get(f"{ZENODO_API}/deposit/depositions/{state['deposit_id']}", headers=headers())
    check(r, {200})
    dep = r.json()
    if dep.get("submitted"):
        published = dep
    else:
        r = requests.post(f"{ZENODO_API}/deposit/depositions/{state['deposit_id']}/actions/publish", headers=headers())
        check(r, {200, 201, 202})
        published = r.json()

    doi = published.get("doi") or published.get("metadata", {}).get("doi") or state["doi"]
    if doi != state["doi"]:
        raise RuntimeError(f"Published DOI {doi} does not match reserved DOI {state['doi']}")

    record_id = published.get("record_id") or state.get("record_id") or state["deposit_id"]
    zenodo_url = published.get("links", {}).get("record_html") or published.get("links", {}).get("html") or f"https://zenodo.org/records/{record_id}"
    state.update({"status": "published", "doi": doi, "record_id": record_id, "zenodo_url": zenodo_url})
    write_state(state)
    update_text_files(doi, state["publication_date"], published=True, zenodo_url=zenodo_url)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare", "publish"}:
        raise SystemExit("Usage: python automation/zenodo_publish.py [prepare|publish]")
    if sys.argv[1] == "prepare":
        prepare()
    else:
        publish()
