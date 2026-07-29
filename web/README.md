# T-cell Evidence Workbench

Next.js analyst interface for the registered CD4+ Perturb-seq source-QC workflow in the parent
repository.

## Run locally

Generate or retain the official artifacts under `../output/official`, then:

```powershell
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The server reads the parent repository's generated artifacts directly. To use another equivalent
bundle:

```powershell
$env:ANALYSIS_OUTPUT_DIR = "C:\absolute\path\to\output\official"
npm run dev
```

At startup, the app fingerprints the bundle manifest. Every table read is checked against the
SHA-256 recorded in that manifest, and cached without revalidation under the manifest fingerprint.
Restart the app when intentionally switching bundles.

## Available workspaces

- `/` — registered-run overview and filter funnel
- `/explore` — searchable, sortable eligible candidate table
- `/genes/[gene]` — gene dossier with a React Flow + ELK evidence graph
- `/compare` — side-by-side condition and metric comparison
- `/robustness` — exploratory score-component reweighting
- `/findings` — constrained Markdown finding-card generator
- `/provenance` — source, contract, package, and artifact ledger

The evidence graph supports search-to-focus, hover and persistent neighborhood highlighting,
connected-evidence navigation, annotation and provenance filters, relation labels, horizontal and
vertical layouts, draggable nodes, zoom, fit, reset, and a desktop minimap. The UI uses a cohesive
dark scientific-workbench theme.

## Reviewer and publishing layer

- The fixed reviewer dock provides a route-aware four-step review through the overview, candidate
  explorer, evidence graph, and finding card.
- Reviewer feedback remains in the browser until the reviewer explicitly copies, downloads, or
  opens an email draft. Set `NEXT_PUBLIC_REVIEW_FEEDBACK_EMAIL` to show the email-draft action.
- Vercel Web Analytics and Speed Insights strip queries, fragments, and dynamic gene identifiers
  before transmission.
- Client and server failures emit privacy-scrubbed structured events to Vercel Runtime Logs. Error
  messages omit stack traces, headers, user-agent strings, email addresses, URLs, and local paths.
- The overview screenshot under `public/t-cell-evidence-overview.png` supplies the Open Graph and
  large social-card image.

## Scientific boundary

The interface does not change or strengthen the analysis contract. It presents source-QC
prioritization results and clearly separates registered outputs from exploratory scenarios.
Candidate labels are not independent verification, experimental validation, causal proof, or
therapeutic recommendations.

## Checks

```powershell
npm run lint
npm run typecheck
npm run build
```
