.PHONY: lint typecheck check

lint:
	ruff check src/ packages/

typecheck:
	mypy src/ packages/

check: lint typecheck
