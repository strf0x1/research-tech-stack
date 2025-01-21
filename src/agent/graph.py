import asyncio
from typing import cast, Any, Literal
import json
import os
from typing import Optional

from tavily import AsyncTavilyClient
from langchain_anthropic import ChatAnthropic
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, StateGraph
from pydantic import BaseModel, Field

from agent.configuration import Configuration
from agent.state import InputState, OutputState, OverallState
from agent.utils import deduplicate_and_format_sources, format_all_notes
from agent.prompts import (
    EXTRACTION_PROMPT,
    REFLECTION_PROMPT,
    INFO_PROMPT,
    QUERY_WRITER_PROMPT,
)

# LLMs

rate_limiter = InMemoryRateLimiter(
    requests_per_second=4,
    check_every_n_seconds=0.1,
    max_bucket_size=10,  # Controls the maximum burst size.
)
claude_3_5_sonnet = ChatAnthropic(
    model="claude-3-5-sonnet-latest", temperature=0, rate_limiter=rate_limiter
)

# Search

tavily_api_key: Optional[str] = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError(
        "TAVILY_API_KEY environment variable is required. Please set it with your Tavily API key."
    )
tavily_async_client = AsyncTavilyClient(api_key=tavily_api_key)


class Queries(BaseModel):
    queries: list[str] = Field(
        description="List of search queries.",
    )


class ReflectionOutput(BaseModel):
    is_satisfactory: bool = Field(
        description="True if all required technology choices are well specified and justified"
    )
    missing_components: list[str] = Field(
        description="List of technology components that are missing or need better justification"
    )
    search_queries: list[str] = Field(
        description="If is_satisfactory is False, provide 1-3 targeted search queries to find information about missing components"
    )
    reasoning: str = Field(description="Brief explanation of the assessment")


def generate_queries(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Generate search queries based on the project description and tech stack requirements."""
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_search_queries = configurable.max_search_queries

    # Generate search queries
    structured_llm = claude_3_5_sonnet.with_structured_output(Queries)

    # Format system instructions
    query_instructions = QUERY_WRITER_PROMPT.format(
        project_description=state.project_description,
        info=json.dumps(state.extraction_schema, indent=2),
        user_requirements=state.user_requirements,
        max_search_queries=max_search_queries,
    )

    # Generate queries
    results = cast(
        Queries,
        structured_llm.invoke(
            [
                {"role": "system", "content": query_instructions},
                {
                    "role": "user",
                    "content": "Please generate a list of search queries to find optimal technology choices.",
                },
            ]
        ),
    )

    # Queries
    query_list = [query for query in results.queries]
    return {"search_queries": query_list}


async def research_tech_stack(
    state: OverallState, config: RunnableConfig
) -> dict[str, Any]:
    """Execute a multi-step web search and information extraction process for tech stack research.

    This function performs the following steps:
    1. Executes concurrent web searches using the Tavily API
    2. Deduplicates and formats the search results
    3. Extracts relevant technical information
    """

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_search_results = configurable.max_search_results

    try:
        # Search tasks
        search_tasks = []
        for query in state.search_queries:
            search_tasks.append(
                tavily_async_client.search(
                    query,
                    max_results=max_search_results,
                    include_raw_content=True,
                    topic="technology",
                )
            )

        # Execute all searches concurrently
        search_docs = await asyncio.gather(*search_tasks)

        # Deduplicate and format sources
        source_str = deduplicate_and_format_sources(
            search_docs, max_tokens_per_source=1000, include_raw_content=True
        )

    except Exception as e:
        # If search fails, create a fallback response focusing on general best practices
        fallback_content = f"""
        Unable to perform live research due to an error: {str(e)}
        
        Proceeding with general best practices and common technology patterns for the given requirements.
        Note: These recommendations will be based on general knowledge rather than current research.
        
        Consider visiting the following resources manually:
        - GitHub trending repositories
        - Technology comparison sites
        - Stack Overflow insights
        - Tech blogs and case studies
        """
        source_str = fallback_content

    # Generate structured notes about technology choices
    p = INFO_PROMPT.format(
        info=json.dumps(state.extraction_schema, indent=2),
        content=source_str,
        project_description=state.project_description,
        user_requirements=state.user_requirements,
    )
    result = await claude_3_5_sonnet.ainvoke(p)
    return {"completed_notes": [str(result.content)]}


def extract_tech_recommendations(state: OverallState) -> dict[str, Any]:
    """Gather research notes and extract concrete technology recommendations."""

    # Format all notes
    notes = format_all_notes(state.completed_notes)

    # Extract schema fields
    system_prompt = EXTRACTION_PROMPT.format(
        info=json.dumps(state.extraction_schema, indent=2), notes=notes
    )
    structured_llm = claude_3_5_sonnet.with_structured_output(state.extraction_schema)
    result = structured_llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Based on the research notes, recommend a concrete tech stack that matches the requirements.",
            },
        ]
    )
    return {"info": result}


def reflection(state: OverallState) -> dict[str, Any]:
    """Reflect on the recommended tech stack and identify any gaps or missing justifications."""
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionOutput)

    # Format reflection prompt
    system_prompt = REFLECTION_PROMPT.format(
        schema=json.dumps(state.extraction_schema, indent=2),
        info=state.info,
    )

    # Invoke
    result = cast(
        ReflectionOutput,
        structured_llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Evaluate the completeness and justification of the tech stack recommendations."},
            ]
        ),
    )

    if result.is_satisfactory:
        return {"is_satisfactory": result.is_satisfactory}
    else:
        return {
            "is_satisfactory": result.is_satisfactory,
            "search_queries": result.search_queries,
            "reflection_steps_taken": state.reflection_steps_taken + 1,
        }


def route_from_reflection(
    state: OverallState, config: RunnableConfig
) -> Literal[END, "research_tech_stack"]:  # type: ignore
    """Route the graph based on the reflection output."""
    # Get configuration
    configurable = Configuration.from_runnable_config(config)

    # If we have satisfactory recommendations, end the process
    if state.is_satisfactory:
        return END

    # If recommendations aren't satisfactory but we haven't hit max steps, continue research
    if state.reflection_steps_taken <= configurable.max_reflection_steps:
        return "research_tech_stack"

    # If we've exceeded max steps, end even if not satisfactory
    return END


# Add nodes and edges
builder = StateGraph(
    OverallState,
    input=InputState,
    output=OutputState,
    config_schema=Configuration,
)
builder.add_node("extract_tech_recommendations", extract_tech_recommendations)
builder.add_node("generate_queries", generate_queries)
builder.add_node("research_tech_stack", research_tech_stack)
builder.add_node("reflection", reflection)

builder.add_edge(START, "generate_queries")
builder.add_edge("generate_queries", "research_tech_stack")
builder.add_edge("research_tech_stack", "extract_tech_recommendations")
builder.add_edge("extract_tech_recommendations", "reflection")
builder.add_conditional_edges("reflection", route_from_reflection)

# Compile
graph = builder.compile()
