.PHONY: venv
venv:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt