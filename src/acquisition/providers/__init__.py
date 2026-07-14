"""
src/acquisition/providers/__init__.py

Importing this package triggers self-registration of all provider classes.
The ProviderRegistry imports this package once at startup.

To add a new provider:
  1. Create src/acquisition/providers/my_board.py
  2. Add the import below
  3. Add config/providers/my_board.yaml
  NO other changes required.
"""
# ruff: noqa: F401
from src.acquisition.providers import naukri
from src.acquisition.providers import remoteok
from src.acquisition.providers import weworkremotely
from src.acquisition.providers import google_jobs
from src.acquisition.providers import wellfound
from src.acquisition.providers import instahyre
from src.acquisition.providers import foundit
