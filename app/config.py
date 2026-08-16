from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")
MIN_SIGNIFICANCE_SCORE = int(os.getenv("MIN_SIGNIFICANCE_SCORE", "70"))
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "30"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
