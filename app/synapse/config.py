import os

SYNAPSE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "synapse"
)
AGENTS_FILE = os.path.join(SYNAPSE_DIR, "agents.json")
PATTERNS_FILE = os.path.join(SYNAPSE_DIR, "learned_patterns.json")
FEEDBACK_FILE = os.path.join(SYNAPSE_DIR, "feedback.json")

MAX_DEBATE_ROUNDS = 3
MAX_AGENTS_IN_DEBATE = 4

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_VERIFICATION_TOKEN = os.environ.get("FEISHU_VERIFICATION_TOKEN", "")
FEISHU_ENCRYPT_KEY = os.environ.get("FEISHU_ENCRYPT_KEY", "")