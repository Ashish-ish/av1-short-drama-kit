.PHONY: all check test bench demo-encode clean help

PYTHON ?= PYTHONPATH=. python3
NODE ?= node

all: check

help:
	@echo "AV1 Adoption Kit for Vertical Drama Apps"
	@echo ""
	@echo "Available commands:"
	@echo "  make demo-encode   Run reproducible encode pipeline on bundled 10s vertical clip"
	@echo "  make bench         Run full multi-codec benchmark, calculate BD-rates, generate RD curves"
	@echo "  make check         Execute full validation suite (Python & React Native tests)"
	@echo "  make clean         Remove build artifacts and temporary files"
	@echo ""

demo-encode:
	@echo "==> Running demo encode on bundled 10-second vertical clip..."
	$(PYTHON) harness/encode.py --input test_assets/bundled_demo_vertical.mp4 --output dist/demo_hls --codecs h264 hevc av1 --rungs 360p 540p 720p --category talking_head --mock
	@echo "==> Demo encode complete. Manifests and fMP4 segments generated in dist/demo_hls"

bench:
	@echo "==> Running full multi-codec BD-rate & VMAF benchmark..."
	$(PYTHON) harness/vmaf_bd_rate.py --output-json docs/research/bd_rate_results.json --output-csv docs/research/bd_rate_results.csv
	@echo "==> Generating research reports and SVG Rate-Distortion curves..."
	$(PYTHON) harness/generate_report.py --eval-json docs/research/bd_rate_results.json --output-md docs/research/research_report.md --output-curves-dir docs/research/curves
	@echo "==> Benchmark complete. Reports in docs/research/"

check:
	@echo "==> Running Python harness unit tests..."
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"
	@echo "==> Running React Native bridge unit tests..."
	$(NODE) --test react-native/tests/*.test.js
	@echo "==> Verifying research files and curves exist..."
	test -f docs/research/bd_rate_results.json
	test -f docs/research/bd_rate_results.csv
	test -f docs/research/research_report.md
	test -f docs/research/curves/rd_curve_540p.svg
	@echo "==> All checks passed successfully!"

clean:
	rm -rf dist/
	rm -rf /tmp/test_cmaf_papr /tmp/test_master_av1.m3u8
	find . -type d -name "__pycache__" -exec rm -rf {} +
