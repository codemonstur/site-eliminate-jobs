# eliminate-jobs

Static site listing **every profession tracked by the U.S. Department of Labor**
(O*NET-SOC database): 1,016 occupations, with a live search box and pagination
so the page stays small.

## Structure

| Path                          | What it is                                              |
|-------------------------------|---------------------------------------------------------|
| `static/`                     | Site source (`index.html`, `style.css`, `app.js`, `professions.js`) |
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
after updating the CSV.

## Hosting on GitHub Pages

1. Push the repository to GitHub.
2. **Settings → Pages → Source: GitHub Actions**.
3. Push to `main` — the workflow builds `wwwroot/` and deploys it.

The site is fully static: relative links only, no server-side code, no
third-party CDNs.

## Data source

[O*NET OnLine](https://www.onetonline.org/find/all), sponsored by the U.S.
Department of Labor, Employment and Training Administration.
