# Verification Literacy website

A static copy of the owner’s Tilda website, preserving its original HTML, visual styling, and responsive layouts. The public website is in `dist/`.

## Preview

Run `python3 -m http.server 8000 --directory dist`, then open http://localhost:8000.

## Publish on GitHub Pages

1. Upload this project to a new GitHub repository, including the `.github` directory.
2. In the repository, open **Settings → Pages** and select **GitHub Actions** as the source.
3. Push to `main`, or run **Publish website to GitHub Pages** from the Actions tab.
4. The workflow displays the published URL when deployment succeeds.

No build or package installation is required. All website paths are relative to support repository subdirectories.

## Migration notes

See `mirror-report.json` for exactly which pages and assets were copied and any download failures. Pages that could not be downloaded remain linked to the original Tilda website. Tilda-hosted blog feeds, analytics, forms, and embedded services may still depend on Tilda; newsletter submission has not been verified on a new domain. Static hosting alone does not replace those services.

The original Tilda markup and scripts are preserved for visual fidelity. Edit the HTML in `dist/` to change the content. `scripts/mirror.py` is an optional download utility; rerunning it overwrites the copied pages.
