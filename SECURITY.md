# Security and data handling

Audience Mirror is intended to process unreleased media, product environments,
simulation traces, and research data. The
current runnable baseline does not include a production deployment. The local
workbench can accept authorized local media, but it is not an approved private
pilot environment and must not be exposed to untrusted networks.

## Do not commit

- unreleased or restricted media;
- customer, participant or employee identities;
- eye-tracking, physiological, transaction or account-level records;
- API keys, cookies, signed URLs or production logs;
- Persona datasets whose source or license has not been reviewed;
- generated artifacts containing any of the above.

## Local baseline and workbench

The checked-in fixture is wholly synthetic. The deterministic runtime makes no
network calls and incurs no model cost. Generated artifacts are written under
the ignored `artifacts/` directory. Local video ingest also stays under that
directory by default.

Remote model processing is denied by default and must be confirmed for each
actual call against the selected provider, model and current policy profile;
the confirmation does not persist to the next call. The public Gemini adapter
rejects `confidential` and `restricted` assets. This gate is not a substitute
for confirming provider retention, training use, region, deletion and customer
authorization. The FastAPI server
stores experiment state in memory and has no authentication, tenant isolation,
malware scanning or production-grade upload controls; keep the default
`127.0.0.1` binding.

## Before a private pilot

Confirm media rights, purpose, processors, model-training use, retention,
region, tenant isolation, export policy, watermarking and deletion receipts.
Human withdrawal must invalidate derived claims, caches and exports.

Report suspected accidental data exposure privately to the repository owner;
do not open a public issue containing the affected data.
