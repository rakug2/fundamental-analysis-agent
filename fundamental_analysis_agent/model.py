"""The LLM every agent uses: OpenAI's gpt-4o-mini, through Strands.

Reads the keys from fundamental_analysis_agent/.env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from strands.models.openai import OpenAIModel

load_dotenv(Path(__file__).parent / ".env")

model = OpenAIModel(
    client_args={"api_key": os.environ["OPENAI_API_KEY"]},
    model_id="gpt-4o-mini",
)
