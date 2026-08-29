.PHONY: preview dependencies test render deploy login

PREVIEW_URL := http://127.0.0.1:5000

preview: dependencies render
	@echo "Once the emulators are ready, open: $(PREVIEW_URL)"
	@quarto preview --no-serve --no-browser & \
	quarto_pid=$$!; \
	trap 'kill "$$quarto_pid" 2>/dev/null || true' EXIT INT TERM; \
	npx firebase-tools@latest emulators:start --only hosting,functions

dependencies:
	npm --prefix functions ci

test: dependencies
	npm --prefix functions test

render:
	quarto render

deploy: test render
	npx firebase-tools@latest deploy --only hosting

login:
	npx firebase-tools@latest login
