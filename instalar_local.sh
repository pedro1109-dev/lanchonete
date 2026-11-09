#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 configurar.py
python3 -m venv .venv
.venv/bin/python -m pip install -r sistema/requirements.txt
export USE_SQLITE=1 DEBUG=1
.venv/bin/python sistema/manage.py migrate
.venv/bin/python sistema/manage.py seed_demo
exec .venv/bin/python sistema/manage.py runserver
