from dataclasses import dataclass, field
from typing import Any, Optional, Annotated
import operator


DEFAULT_EXTRACTION_SCHEMA = {
    "title": "TechStackRecommendation",
    "description": "Recommended technology stack for a software application",
    "type": "object",
    "properties": {
        "frontend": {
            "type": "object",
            "properties": {
                "framework": {
                    "type": "string",
                    "description": "Main frontend framework/library recommendation"
                },
                "ui_libraries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Recommended UI component libraries and tools"
                },
                "justification": {
                    "type": "string",
                    "description": "Explanation for the frontend technology choices"
                }
            },
            "required": ["framework"]
        },
        "backend": {
            "type": "object",
            "properties": {
                "framework": {
                    "type": "string",
                    "description": "Main backend framework recommendation"
                },
                "database": {
                    "type": "string",
                    "description": "Recommended database solution"
                },
                "hosting": {
                    "type": "string",
                    "description": "Recommended hosting/cloud platform"
                },
                "justification": {
                    "type": "string",
                    "description": "Explanation for the backend technology choices"
                }
            },
            "required": ["framework", "database"]
        },
        "additional_services": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "purpose": {"type": "string"},
                    "justification": {"type": "string"}
                }
            },
            "description": "Additional services, APIs, or tools recommended"
        },
        "deployment": {
            "type": "object",
            "properties": {
                "ci_cd": {
                    "type": "string",
                    "description": "Recommended CI/CD solution"
                },
                "monitoring": {
                    "type": "string",
                    "description": "Recommended monitoring and logging solutions"
                }
            }
        },
        "estimated_complexity": {
            "type": "string",
            "enum": ["Low", "Medium", "High"],
            "description": "Estimated complexity of implementing this stack"
        }
    },
    "required": ["frontend", "backend"]
}


@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    project_description: str
    "Project description provided by the user."

    extraction_schema: dict[str, Any] = field(
        default_factory=lambda: DEFAULT_EXTRACTION_SCHEMA
    )
    "The json schema defines the tech stack information the agent is tasked with recommending."

    user_requirements: Optional[dict[str, Any]] = field(default=None)
    "Any specific requirements or constraints from the user."


@dataclass(kw_only=True)
class OverallState:
    """Overall state that tracks the progress of tech stack research and recommendations."""

    project_description: str
    "Project description provided by the user."

    extraction_schema: dict[str, Any] = field(
        default_factory=lambda: DEFAULT_EXTRACTION_SCHEMA
    )
    "The json schema defines the tech stack information the agent is tasked with recommending."

    user_requirements: str = field(default=None)
    "Any specific requirements or constraints from the user."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant technology information"

    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the tech stack"

    info: dict[str, Any] = field(default=None)
    """
    A dictionary containing the recommended tech stack and justifications
    based on the user's requirements and the graph's execution.
    This is the primary output of the recommendation process.
    """

    is_satisfactory: bool = field(default=None)
    "True if all required tech stack components are well defined, False otherwise"

    reflection_steps_taken: int = field(default=0)
    "Number of times the reflection node has been executed"


@dataclass(kw_only=True)
class OutputState:
    """The response object for the end user."""

    info: dict[str, Any]
    """
    A dictionary containing the recommended tech stack and justifications
    based on the user's requirements and the graph's execution.
    This is the primary output of the recommendation process.
    """
