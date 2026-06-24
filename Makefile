.PHONY: lint typecheck check

lint:
	ruff check src/

typecheck:
	mypy src/

check: lint typecheck
