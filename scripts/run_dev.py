"""Szybkie uruchomienie Papugi bez pakowania — do developmentu/testów."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from papuga.main import main

if __name__ == "__main__":
    main()
