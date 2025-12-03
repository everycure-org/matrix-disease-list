# Make sure OPENAI_API_KEY is set in your environment before running this script
set -e
chmod +x setup_ollama.sh && ./setup_ollama.sh
chmod +x install_kedro.sh && ./install_kedro.sh
cd llm-disease-categorization
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
kedro run
cd ..
