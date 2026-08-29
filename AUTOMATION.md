# Publication automation

Execution Intelligence v1.0 is configured for an automated GitHub -> Zenodo publication workflow.

## Why this uses a custom workflow

Zenodo's native GitHub integration is designed around archiving GitHub **software** releases. Execution Intelligence is a **publication / concept paper**, so this repository uses the Zenodo REST API instead. This preserves the correct Zenodo resource type while still allowing GitHub to drive the release process.

## One-time requirement

Create a Zenodo personal access token with these scopes:

- `deposit:write`
- `deposit:actions`

Store it in this GitHub repository as an Actions secret named exactly:

`ZENODO_TOKEN`

Never commit or paste the token into repository files.

## What the workflow does

The workflow `.github/workflows/publish-v1.yml` performs the v1.0 publication end to end:

1. Creates or reuses a Zenodo draft.
2. Obtains Zenodo's pre-reserved DOI through the REST API.
3. Writes the DOI into the publication source and citation metadata.
4. Builds the final PDF reproducibly from `paper.md`.
5. Fails if the PDF is not exactly **12 pages**.
6. Uploads the final PDF to the Zenodo draft.
7. Commits the DOI and final PDF to GitHub.
8. Creates the GitHub `v1.0` release and attaches the same PDF.
9. Publishes the Zenodo record.
10. Writes the final Zenodo record URL/status back into GitHub.

The authoritative publication file is:

`dist/Execution_Intelligence_Judgement_Carried_into_Execution_v1.0.pdf`

## Trigger

The workflow can be run manually from GitHub Actions.

It can also be triggered by committing/changing:

`.publication/PUBLISH`

The PUBLISH marker is intentionally not created until the Zenodo token has been configured.

## Safety / repeatability

The workflow stores Zenodo draft state in:

`.publication/zenodo-state.json`

If a run stops after a DOI has been reserved, a subsequent run reuses that Zenodo draft instead of intentionally creating a new DOI.

A published v1.0 deposit is treated as final. Future substantive publication updates should use Zenodo versioning rather than overwriting the v1.0 record.
