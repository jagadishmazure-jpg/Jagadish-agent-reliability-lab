# Make the repo root importable so tests can import the top-level
# packages (carenv, tasks, agents, scoring) without installation.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
