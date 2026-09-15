# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, and others that honor AGENTS.md) when working with code in this repository.

## What this is

Grid Surfer is a Streamlit web app for exploratory analysis of tabular datasets (CSV/TSV/JSON). It shows data in a filterable/sortable AgGrid, descriptive statistics, and Altair-based charts (histogram, dot plot, scatter/XY plot) with grouping and faceting. Live demo: https://grid-surfer.streamlit.app/

## Commands

Dependency management and running the app use `uv` (dependencies are declared in `pyproject.toml`, locked in `uv.lock`).

```bash
# Run the app locally (from repo root)
uv run streamlit run app.py

# Lint (line length capped at 79 in ruff.toml, with E501 explicitly enabled)
uv run ruff check .
```

There is no test suite currently (the `tests/` directory is a placeholder with an empty `tests/data/` subfolder). The devcontainer is preconfigured for pytest against `tests/` if tests are added later.

### Docker

```bash
./build-docker.sh [tag]   # builds using buildx, tags the image, stamps version from `git describe`
./deploy.sh [tag]         # builds (via build-docker.sh) then runs the container, replacing any existing one
```

The Dockerfile is a two-stage build: a `builder` stage that runs `uv sync --locked --no-dev`, and a slim `runtime` stage that copies the venv plus `app.py`, `src/`, `assets/`, `data/`, and `.streamlit/`. The app runs as a non-root user and exposes port 8501 with a healthcheck against `/_stcore/health`.

## Architecture

- `app.py` — entry point. Sets Streamlit page config, initializes custom CSS and session state, renders the sidebar and the "Load data" dialog (file upload or a bundled demo dataset), then delegates to `render_body`.
- `src/ui/gs_state.py` — session state initialization/helpers. Demo dataset metadata is loaded from `data/demo_datasets.json` (cached with `@st.cache_data`); each entry has a `source` of either `vega-dataset` (loaded via `vega_datasets.local_data`) or `local-dataset` (a file under `data/`).
- `src/ui/gs_utils.py` — shared helpers used across plot modules: dataframe column-type detection (`get_df_column_types` — splits columns into numeric vs. categorical), Altair scale construction, chart-download naming, the app version lookup (`version.txt` at build time, falling back to `git describe` in dev), and the status-bar updater.
- `src/ui/gs_body.py` — the main render pipeline: loads the selected data source (`data_loader`, cached), applies the optional conditional-filter UI (`filter_dataframe`), renders the AgGrid table (`render_grid`), and drives the plot-type selector (`st.pills`: Describe / Histogram / Dot / Scatter) that dispatches to the modules below.
- `src/ui/describe.py`, `distplot.py`, `dotplot.py`, `xyplot.py` — one module per visualization. Each follows the same pattern: an options-gathering function that renders Streamlit sidebar widgets into an `opts` dict (plus an `opts_type` dict grouping option keys by target, e.g. `mark`/`scale`), and a plotting function that consumes `opts`/`opts_type` to build/render an Altair chart. New chart types should follow this same options/render split.

Data flow is grid-centric: the AgGrid return value (`grid_return`, filtered/sorted via `DataReturnMode.FILTERED_AND_SORTED`) is what gets passed into each plot module, so charts always reflect the current grid filter/sort state, not just the raw loaded dataframe.

Demo datasets live in `data/`; `data/save_demos.py` is a utility script for regenerating/saving them.
