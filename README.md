# Ai-verfication — Verification Literacy website

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

See `mirror-report.json` for exactly which pages and assets were copied and any download failures. The homepage, blog, three language landing pages (English, Turkish, Russian), and all 18 module editions are hosted locally. The Russian landing page and the Turkish/Russian modules were generated from the available English source because those editions were not published on Tilda. These pages are labeled as automatic translations. Translation dictionaries are bundled locally; visitors do not call a translation service. Text inside source images, citations, and embedded audio/video can remain in the original language. Tilda-hosted blog feeds, analytics, forms, and embedded services may still depend on Tilda; newsletter submission has not been verified on a new domain. Static hosting alone does not replace those services.

The original Tilda markup and scripts are preserved for visual fidelity. Edit the HTML in `dist/` to change the content. `scripts/mirror.py` is an optional download utility; rerunning it overwrites the copied pages.


## Course navigation and translations

Shared navigation provides a home link, all six modules, and EN/TR/RU switching on each course page. Embedded exercises run in isolated scopes so controls in one activity cannot attach handlers to another activity. Answer values remain in their source form; only presentation text is translated.

The `scripts/` utilities are development helpers, not deployment dependencies. `localize-course.py` extracts public source text and uses a translation service during generation; its JavaScript extraction helper expects Acorn installed with `npm install --prefix /tmp/verification-localize acorn`. `prepare-course-editions.py` applies reviewed terminology, builds the language navigation, and prepares the missing language editions. `finalize-course.py` renders static translations and isolates exercise scripts. Run them in that order after mirroring. Do not rerun the mirror alone on the completed editions: it overwrites migrated source pages.

`course-check-report.json` records browser checks across 21 language/module pages, including quiz interaction and language checks. The source-download failures in `mirror-report.json` describe missing original Tilda pages; the final missing editions were generated locally as described above.


Platform promotion blocks, platform favicons, old page metadata, DNS-prefetch hints, and analytics loaders are removed by `scripts/remove-platform-branding.py`. The local layout and exercise assets remain available for compatibility. Run this cleanup after regeneration.
