#!/bin/sh
R -e "knitr::knit('main.Rnw')"
R -e "knitr::knit('tex/results.Rnw', 'tex/results.tex')"
