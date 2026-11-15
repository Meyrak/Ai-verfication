# AI-Assisted Verification Literacy

An interactive, multilingual coursebook for journalists, journalism students, educators, and media professionals. Learn to assess claims, investigate visual content, evaluate AI-generated information, and make responsible editorial decisions.

**Live website:** https://meyrak.github.io/Ai-verfication/

## Languages

- [English](https://meyrak.github.io/Ai-verfication/en/)
- [Türkçe](https://meyrak.github.io/Ai-verfication/tr/)
- [Русский](https://meyrak.github.io/Ai-verfication/ru/)

Each language edition includes six modules. The navigation bar provides direct module access and language switching in the same browser tab.

## Course modules

1. **Verification Mindset and AI Literacy** — critical thinking, information disorder, and human oversight.
2. **Smart Skepticism, Ethics, and Human-in-the-Loop** — hallucinations, bias, transparency, privacy, and accountability.
3. **The Verifier’s Toolkit** — tool selection, reverse image search, source checks, and investigation workflows.
4. **Applied Text and Claim Verification** — evaluating claims, quotations, statistics, and source credibility.
5. **Visual, Video, and Deepfake Verification** — keyframes, metadata, visual inconsistencies, and synthetic media.
6. **Integrated Workflow Scenarios** — newsroom simulations, deadline decisions, and a final assessment.

Activities include quizzes, flashcards, checklists, and branching newsroom scenarios. The [blog](https://meyrak.github.io/Ai-verfication/blog/) provides additional reading.

## Preview locally

From the project directory, run:

```sh
python3 -m http.server 8000 --directory dist
```

Open http://localhost:8000 in your browser. No package installation or build step is required.

## Edit and publish

The website files are in `dist/`. Edit the corresponding HTML pages, stylesheets, or translation dictionaries, then commit and push to `main`.

The included workflow, `.github/workflows/pages.yml`, publishes `dist/` through GitHub Pages. The repository’s **Settings → Pages → Source** must be set to **GitHub Actions**. Deployment progress appears in the repository’s **Actions** tab.

## Project files

- `dist/index.html` — homepage.
- `dist/en/`, `dist/tr/`, `dist/ru/` — language landing pages.
- `dist/module1/` through `dist/module6/` — English, Turkish, and Russian module editions.
- `dist/blog/` — blog page.
- `dist/assets/` — local images, fonts, styles, scripts, and translation dictionaries.
- `scripts/` — optional content preparation and browser-check utilities.
- `course-check-report.json` and `navigation-check-report.json` — recorded browser checks.

## Translation and service notes

Some language editions were automatically translated from the English course and are labeled accordingly. Translation dictionaries are served locally. Text inside images, quotations, and embedded audio or video may remain in its original language.

Embedded media requires an internet connection. Newsletter submission is not configured as a working subscription service.

Development utilities can overwrite generated pages. Back up manual content changes before running them. They are not needed for normal editing or deployment.
