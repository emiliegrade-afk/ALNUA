import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from skills.skill_chroma import index_project_docs

print("Indexation des docs ALNUA...")
index_project_docs()
print("Done !")
