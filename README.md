# Langchain Research Agent 
This project was based on the [Company Researcher Agent](https://github.com/langchain-ai/company-researcher) project. 

## Quickstart

Clone the repository and launch the assistant:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/langchain-ai/company-researcher.git
cd company-researcher
export TAVILY_API_KEY=your_tavily_api_key
export ANTHROPIC_API_KEY=your_anthropic_api_key
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev
```

## Configuration

The configuration for Company Researcher Agent is defined in the `src/agent/configuration.py` file: 
* `max_search_queries`: int = 3 # Max search queries per company
* `max_search_results`: int = 3 # Max search results per query
* `max_reflection_steps`: int = 1 # Max reflection steps
