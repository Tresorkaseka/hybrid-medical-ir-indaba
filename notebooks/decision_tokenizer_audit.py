# @title 7. Vérifier le tokenizer du runtime contre le fichier officiel et exporter
from tokenizers import Tokenizer
import zipfile
raw_tokenizer_path = pathlib.Path(model._source) / "tokenizer.json"
raw_tokenizer = Tokenizer.from_file(str(raw_tokenizer_path))
runtime_tokenizer = model.runtime.backend.tokenizer
audit_texts = list(payload["queries"].values()) + list(payload["trials"].values())
for pair in payload["benchmark_pairs"]:
    audit_texts.append(json.dumps(decision_request(payload["queries"][pair["query_key"]], payload["trials"][pair["trial_id"]]), ensure_ascii=False))
mismatches = []
for index, text in enumerate(audit_texts):
    expected_ids = raw_tokenizer.encode(text, add_special_tokens=False).ids
    actual_ids = runtime_tokenizer.encode(text, add_special_tokens=False)
    if expected_ids != actual_ids:
        mismatches.append({"index": index, "n_raw": len(expected_ids), "n_runtime": len(actual_ids)})
audit = {"n_texts": len(audit_texts), "n_matching": len(audit_texts)-len(mismatches), "mismatches": mismatches, "tokenizer_sha256": hashlib.sha256(raw_tokenizer_path.read_bytes()).hexdigest(), "warning_disposition": "IDs compared with packaged tokenizer.json; no regex override"}
report["tokenizer_audit"] = audit
REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
print(json.dumps(audit, indent=2))
with zipfile.ZipFile("decision_benchmark_bundle.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
    for path in [REPORT_PATH, LOCK_PATH, PARTIAL_PATH]:
        if path.exists():
            bundle.write(path, path.name)
files.download("decision_benchmark_bundle.zip")
if mismatches:
    raise RuntimeError("Tokenisation différente du fichier officiel : examiner avant D/E")
