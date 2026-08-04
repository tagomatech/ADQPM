# Publishing the public book

The public `course/` project is designed to publish as a static Quarto book. The separate `bloomberg-lab/` project must not be included in the public repository.

## Recommended hosting

Use a public GitHub repository with GitHub Pages and GitHub Actions. GitHub Pages is available for public repositories on GitHub Free. The included workflow renders the book on every push to `main`, uploads `_site`, and deploys it to Pages.

The resulting address will normally be:

```text
https://<github-user>.github.io/<repository-name>/
```

## First publication

1. Create a new public repository for the contents of this `course/` directory.
2. Do not copy `bloomberg-lab/`, private data, Bloomberg extracts, or terminal-specific configuration into that repository.
3. Push the public project to the `main` branch.
4. In the repository settings, open **Pages**, select **GitHub Actions** as the build and deployment source, and approve the `github-pages` environment if GitHub asks for it.
5. Open the Pages URL after the workflow completes.

The workflow installs the Python dependencies and renders with server-generated MathML. It therefore does not require a browser connection to a math-rendering CDN.

## Local check before pushing

```powershell
quarto render
python -m pytest
```

The public source is a living monograph. Revisions should be committed with a short note describing changed theory, empirical design, or implementation behavior. Add a content license and a separate code license before the first public release; do not imply that publication provides accreditation or investment advice.