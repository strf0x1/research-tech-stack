EXTRACTION_PROMPT = """Your task is to take notes gathered from technical research and extract them into a recommended tech stack following this schema.

<schema>
{info}
</schema>

Here are all the notes from research:

<research_notes>
{notes}
</research_notes>

Focus on making concrete, justified recommendations based on the research. Each technology choice should be supported by evidence from the research notes."""

QUERY_WRITER_PROMPT = """You are a technical research query generator tasked with creating targeted search queries to gather information about optimal technology choices.

Here is the project description: {project_description}

Generate at most {max_search_queries} search queries that will help determine the best tech stack according to this schema:

<schema>
{info}
</schema>

<user_requirements>
{user_requirements}
</user_requirements>

Your queries should:
1. Focus on finding recent, real-world implementations of similar systems
2. Target technical blogs, architecture discussions, and case studies
3. Include specific technical requirements mentioned in the project description
4. Search for scalability, performance, and integration patterns
5. Look for comparisons between relevant technology choices

Create focused queries that will help identify the most suitable technologies for this specific use case."""

INFO_PROMPT = """You are researching technology stack recommendations for a project with this description: {project_description}

The following schema shows the type of information we need to recommend:

<schema>
{info}
</schema>

You have just gathered technical content. Your task is to take clear, organized notes about relevant technology choices and patterns.

<Content>
{content}
</Content>

Here are the specific user requirements:
<user_requirements>
{user_requirements}
</user_requirements>

Please provide detailed research notes that:
1. Focus on concrete technology choices and their trade-offs
2. Note specific versions, compatibility requirements, and integration patterns
3. Capture performance characteristics and scalability considerations
4. Include real-world usage examples and case studies when available
5. Highlight any potential challenges or limitations
6. Consider how well each technology aligns with the project requirements

Remember: Don't try to format the output to match the schema yet - just take clear notes that capture all relevant technical information."""

REFLECTION_PROMPT = """You are a technical architect tasked with reviewing the completeness and suitability of a proposed tech stack.

Compare the recommended stack with the required schema and project requirements:

<Schema>
{schema}
</Schema>

Here are the current recommendations:
<recommendations>
{info}
</recommendations>

Analyze if the recommendations are complete and well-justified. Consider:
1. Are all required technology choices specified and justified?
2. Do the recommendations align well with the project requirements?
3. Are there any missing components or integration gaps?
4. Are the justifications based on concrete evidence and research?
5. Have all major technical risks been considered?
6. Is there sufficient information about deployment and scaling?"""
