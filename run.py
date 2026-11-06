#!/usr/bin/env python3
"""Launch CodeForge from a versioned snapshot directory."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import sys
import os

# Oprava pro dynamické spouštění dalších .py souborů v PyInstalleru
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)
    if sys._MEIPASS not in sys.path:
        sys.path.insert(0, sys._MEIPASS)

# EXPLICITNÍ IMPORTY PRO PYINSTALLER
import http.server
import socketserver
import uuid          # <--- OPRAVA PRO TUTO CHYBU
import subprocess    # Často se používá v terminal.py pro spouštění příkazů
import json          # Velmi časté pro konfigurace
import threading     # Nutné pro liveserver na pozadí
import logging       # Často využívané pro logování chyb





def _load_app():
    root = Path(__file__).resolve().parent
    package_name = "codeforge_snapshot"
    package = types.ModuleType(package_name)
    package.__path__ = [str(root)]
    package.APP_NAME = "CodeForge"
    package.__version__ = "3.0.0"
    sys.modules[package_name] = package
    return importlib.import_module(f"{package_name}.app")


def main() -> int:
    app_module = _load_app()
    return app_module.main()


if __name__ == "__main__":
    raise SystemExit(main())
