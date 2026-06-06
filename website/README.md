# LazySkills Website

This folder contains the static GitHub Pages site for LazySkills.

Local preview:

```bash
python3 -m http.server 8080 --directory website
```

Deployment:

- GitHub Actions publishes `website/` through `.github/workflows/pages.yml`.
- The workflow also copies root `skills.json` into the Pages artifact so agents and users can fetch the machine-readable skill index from the website.
- No Node build step is required.

