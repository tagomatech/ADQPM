# Agriculture Derivatives & Quantitative Portfolio Management

This directory contains the executable Quarto research monograph.

## Public book

From this directory:

```powershell
quarto render
```

The public HTML book is written to `_site/index.html`. Equations are converted to static KaTeX during the post-render step, so inline and display formulas do not depend on a browser connection to a math CDN. For a live local version while editing, run:

```powershell
quarto preview
```

## Private Bloomberg companion

Bloomberg connectivity, proprietary extracts, and terminal-specific exercises are maintained in the separate `../bloomberg-lab/` project. It is intentionally outside the public Quarto book and should not be published without checking data rights and the treatment of derived observations.

From the companion project directory, render the private lab with:

```powershell
quarto render
```

## Run the tests

```powershell
$env:PYTHONPATH = "src"
python -m pytest
```

The research code preserves contract identity, delivery dates, settlement fields, quotation units, and data provenance. It is the implementation track of the monograph: every new model should have a clear market object, a testable accounting identity, and an auditable data lineage. Continuous futures may be generated for visualization, but they do not replace contract-level input.