SHELL := /bin/sh

.PHONY: help test quality parse-srd release clean

.DEFAULT_GOAL := help

test:
	uv run pytest

quality:
	@test -n "$(PDF)" || (printf '%s\n' 'Usage: make quality PDF=path/to/srd-5.2.1-it.pdf' && exit 1)
	docker build -f Dockerfile.Parser -t quintaedizione-parser:1.0.0 .
	docker run --rm --entrypoint uv \
		-e SRD_521_IT_PDF=/input.pdf \
		-v "$(abspath $(PDF)):/input.pdf:ro" \
		quintaedizione-parser:1.0.0 \
		run pytest -m full_pdf scripts/parse_srd_v2/tests/test_full_pdf.py

clean:
	rm -rf output dist

parse-srd:
	@test -n "$(PDF)" || (printf '%s\n' 'Usage: make parse-srd PDF=path/to/srd-5.2.1-it.pdf' && exit 1)
	docker build -f Dockerfile.Parser -t quintaedizione-parser:1.0.0 .
	rm -rf output/srd-5.2.1
	mkdir -p output/srd-5.2.1
	docker run --rm \
		-v "$(abspath $(PDF)):/input.pdf:ro" \
		-v "$(CURDIR)/output/srd-5.2.1:/output" \
		quintaedizione-parser:1.0.0 \
		build /input.pdf --output-dir /output

release: parse-srd
	uv run python -m scripts.parse_srd_v2.release output/srd-5.2.1 --dist-dir dist

help:
	@printf '%s\n' \
		'make test' \
		'make quality PDF=path/to/srd-5.2.1-it.pdf' \
		'make parse-srd PDF=path/to/srd-5.2.1-it.pdf' \
		'make release PDF=path/to/srd-5.2.1-it.pdf' \
		'make clean'
