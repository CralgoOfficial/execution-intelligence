# Publication automation

Execution Intelligence v1.0 was published through an automated GitHub -> Zenodo workflow on 29 August 2026.

**DOI:** https://doi.org/10.5281/zenodo.22159150  
**GitHub release:** https://github.com/CralgoOfficial/execution-intelligence/releases/tag/v1.0

## Why this uses a custom workflow

Zenodo's native GitHub integration is designed primarily around archiving GitHub software releases. Execution Intelligence is a **publication / concept paper**, so this repository uses a Zenodo API-driven workflow instead. This preserves the publication-oriented metadata while allowing GitHub to drive the release process.

## Authentication

The workflow uses a Zenodo personal access token stored as a GitHub Actions secret named:

`ZENODO_TOKEN`

The token must never be committed to repository files or logs.

## What the workflow does

The workflow `.github/workflows/publish-v1.yml` performs the publication sequence:

1. Creates or reuses a Zenodo draft.
2. Obtains a pre-reserved DOI.
3. Writes the DOI into the publication source and citation metadata.
4. Builds the final PDF reproducibly from `paper.md`.
5. Fails if the PDF is not exactly **12 pages**.
6. Uploads the final PDF to the Zenodo draft.
7. Commits the DOI and final PDF to GitHub.
8. Creates the GitHub `v1.0` release and attaches the same PDF.
9. Publishes the Zenodo record.
10. Records the final publication state in GitHub.

The authoritative publication file is:

`dist/Execution_Intelligence_Judgement_Carried_into_Execution_v1.0.pdf`

## Publication state

Execution Intelligence v1.0 is now published.

The publication marker is retained at:

`.publication/PUBLISH`

The publication state is retained at:

`.publication/zenodo-state.json`

## Safety / repeatability

A published v1.0 deposit is treated as final. Future substantive updates should use a new Zenodo version rather than overwriting or silently replacing the v1.0 record.

For future Cralgo publications, the same automation pattern can be reused with publication-specific metadata, repository names and page requirements.
