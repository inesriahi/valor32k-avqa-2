import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "data"
REPORT_PATH = ROOT / "data" / "dataset_quality_fix_report.json"

TEMPORAL_EXTRA_OPTIONS = [
    "Both events happen at the same time",
    "Neither event happens in the video",
]

DUPLICATE_OPTION_FIXES = {
    ("jii46gf1UkM", 11397): [
        "SALSA TROMBOLANG",
        "SALSA TROMBOLA",
        "SALSA TROMBONE",
        "SALSA TROMBOLAN",
    ],
    ("RwRKBxqYVN0", 25437): [
        "Anything to Break I am Awesome",
        "Anything to Break Awesome",
        "Anything to Break I am Strong",
        "Anything to Break I am Amazing",
    ],
    ("Arp482w8r_s", 43668): ["Clark Gregg", "Phil Coulson", "Phil Leeb", "Clark Leeb"],
    ("kg7PouRs2Lg", 62412): ["wishies", "wishs", "wish", "wishes"],
    ("4zZiWBp0b08", 63384): [
        "Deskarte Ant Loli",
        "Deskarte Ant Lole",
        "Deskarte Art Loli",
        "Deskarte Ant Loki",
    ],
    ("6dhU9_K2uw8", 68120): ["CE HU 492", "CE HU 429", "P738 SYX", "P783 SYX"],
    ("hIQhby-OLk4", 76187): [
        "Live Falsetto/Whistle",
        "Live Falsetto/Whisper",
        "Live False to Whistle",
        "Live Falsetto Whistle",
    ],
    ("3R8xDvhJk54", 77848): ["G", "e", "C", "A"],
    ("vNFPfWH_Wdc", 96473): [
        "Duchess Vonlit",
        "Duchess Vonlet",
        "Duchess Monlit",
        "Duchess Vondit",
    ],
    ("pp6i-ckuT8I", 105483): ["Asia Tek", "TechAsia", "Asiatech", "TechAsi"],
    ("7enfWOAynno", 118561): [
        "Welcome to Khao Yai National Park",
        "Welcome to Khao Sok National Park",
        "Welcome to Khao Phanom Bencha National Park",
        "Welcome to Khao Lak National Park",
    ],
    ("3ZZDuYU2HM4", 152302): ["Camborne", "Cambourne", "Cambden", "Cambridge"],
}

VALID_MODALITIES = {"visual", "audio", "audio-visual"}
VALID_CATEGORIES = {"relative-position", "description", "action", "temporal", "count", "location"}


def infer_modality(source_tags):
    tags = set(source_tags or [])
    if "audio" in tags and "frames" in tags:
        return "audio-visual"
    if "audio" in tags:
        return "audio"
    return "visual"


def fix_question(question):
    original = copy.deepcopy(question)
    changes = []

    options = question.get("options")
    if isinstance(options, list) and len(options) < 4:
        question["options"] = options + TEMPORAL_EXTRA_OPTIONS[: 4 - len(options)]
        changes.append("expanded_options_to_four")

    qid = question.get("id")
    duplicate_key = (question.get("video_id"), qid)
    if duplicate_key in DUPLICATE_OPTION_FIXES:
        question["options"] = DUPLICATE_OPTION_FIXES[duplicate_key]
        changes.append("deduplicated_options")

    rephrased = question.get("rephrased_answers")
    if isinstance(rephrased, list) and len(rephrased) > 3:
        question["rephrased_answers"] = rephrased[:3]
        changes.append("trimmed_rephrased_answers_to_three")

    if question.get("modality") not in VALID_MODALITIES:
        question["modality"] = infer_modality(question.get("source_tags"))
        changes.append("corrected_invalid_modality")

    if question.get("category") not in VALID_CATEGORIES:
        question["category"] = "description"
        changes.append("corrected_invalid_category")

    if changes:
        return {
            "id": qid,
            "video_id": question.get("video_id"),
            "question": question.get("question"),
            "changes": changes,
            "before": original,
            "after": copy.deepcopy(question),
        }
    return None


def fix_flattened(data):
    report = []
    for item in data:
        change = fix_question(item)
        if change:
            report.append(change)
    return report


def fix_unflattened(data):
    report = []
    for parent in data:
        for question in parent.get("questions", []):
            question.setdefault("video_id", parent.get("video_id"))
            change = fix_question(question)
            if change:
                change["oid"] = parent.get("oid")
                report.append(change)
            question.pop("video_id", None)
    return report


def validate(data, flattened):
    issues = {
        "option_count": 0,
        "duplicate_options": 0,
        "rephrased_count": 0,
        "invalid_modality": 0,
        "invalid_category": 0,
    }
    items = data if flattened else [q for parent in data for q in parent.get("questions", [])]
    for item in items:
        options = item.get("options")
        if not isinstance(options, list) or len(options) != 4:
            issues["option_count"] += 1
        elif len({str(option).strip().lower() for option in options}) != len(options):
            issues["duplicate_options"] += 1

        rephrased = item.get("rephrased_answers")
        if not isinstance(rephrased, list) or len(rephrased) != 3:
            issues["rephrased_count"] += 1

        if item.get("modality") not in VALID_MODALITIES:
            issues["invalid_modality"] += 1
        if item.get("category") not in VALID_CATEGORIES:
            issues["invalid_category"] += 1
    return issues


def main():
    full_report = {}

    for source_path in sorted(SOURCE_DIR.glob("combined_dataset_*.json")):
        flattened = "flattened" in source_path.name
        data = json.loads(source_path.read_text(encoding="utf-8"))
        report = fix_flattened(data) if flattened else fix_unflattened(data)
        validation = validate(data, flattened)

        source_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        full_report[source_path.name] = {
            "changed_samples": len(report),
            "changes": report,
            "post_fix_validation": validation,
        }

    REPORT_PATH.write_text(
        json.dumps(full_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
