# eliminate-jobs

Static site listing **every profession tracked by the U.S. Department of Labor**
(O*NET-SOC database): 1,016 occupations, with a live search box and pagination
so the page stays small. Every profession and every one of the 23 major groups
links to its own detail page, compiled from markdown — major group pages embed
the same search and pagination as the index, driven client-side by `group.js`.

## Structure

| Path                          | What it is                                              |
|-------------------------------|---------------------------------------------------------|
| `static/`                     | Site source (`index.html`, `style.css`, `app.js`, `group.js`, `professions.js`) |
| `arguments/`                  | One markdown page per profession and per major group (1,039 files, generated) |
| `templates/argument.html`     | Pandoc template used to render `arguments/*.md`         |
| `src/generate-pages.py`       | Regenerates `arguments/*.md` from the CSV               |
| `docs/us-occupations-onet-soc.csv` | Same occupation list as CSV (source of truth)       |
| `docs/government-occupational-registries.md` | Overview of government profession registers worldwide |
| `wwwroot/`                    | Build output — the deployable site                      |
| `.github/workflows/pages.yml` | Deploys `wwwroot/` to GitHub Pages                      |

## Build and preview locally

```sh
make build
python3 -m http.server 8899 --directory wwwroot
# open http://localhost:8899
```

The data file `static/professions.js` is generated from the CSV; regenerate it
after updating the CSV. Detail pages work the same way:

```sh
python3 src/generate-pages.py   # rewrite arguments/*.md from the CSV
make build                      # recompile everything into wwwroot/
```

## Hosting on GitHub Pages

1. Push the repository to GitHub.
2. **Settings → Pages → Source: GitHub Actions**.
3. Push to `main` — the workflow builds `wwwroot/` and deploys it.

The site is fully static: relative links only, no server-side code, no
third-party CDNs.

## Data source

[O*NET OnLine](https://www.onetonline.org/find/all), sponsored by the U.S.
Department of Labor, Employment and Training Administration.
