SHELL := /bin/sh

UUID := codex-usage-indicator@noah-be.github.io
SCHEMA := schemas/io.github.noahbe.codex-usage-indicator.gschema.xml
DIST_DIR := dist
PACKAGE := $(DIST_DIR)/$(UUID).shell-extension.zip

.PHONY: all validate test pack install enable live-test clean

all: validate

validate: test
	python3 -m json.tool metadata.json >/dev/null
	glib-compile-schemas --strict --dry-run schemas
	python3 -c 'from pathlib import Path; files = list(Path("bin").glob("*.py")) + list(Path("codex_usage_indicator").glob("*.py")) + list(Path("tests").glob("*.py")); [compile(path.read_text(), str(path), "exec") for path in files]'
	node --check extension.js
	node --check prefs.js

test:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v

pack: validate
	python3 -c 'from pathlib import Path; import shutil; targets = [Path("bin/__pycache__"), Path("codex_usage_indicator/__pycache__"), Path("tests/__pycache__")]; [shutil.rmtree(path) for path in targets if path.is_dir()]'
	mkdir -p $(DIST_DIR)
	gnome-extensions pack --force --out-dir=$(DIST_DIR) \
		--extra-source=bin \
		--extra-source=codex_usage_indicator \
		--extra-source=LICENSE \
		--schema=$(SCHEMA) .

install: pack
	gnome-extensions install --force $(PACKAGE)
	@echo "Installed $(UUID). Log out and back in if GNOME has not loaded it yet."

enable:
	gnome-extensions enable $(UUID)

live-test:
	./bin/codex-usage --format json --pretty

clean:
	python3 -c 'from pathlib import Path; import shutil; targets = [Path("dist"), Path("bin/__pycache__"), Path("codex_usage_indicator/__pycache__"), Path("tests/__pycache__")]; [shutil.rmtree(path) for path in targets if path.is_dir()]'
