import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from tools.web_search import create_book_web_search_tool
from tools.create_prompt import create_veo3_prompt_tool
from tools.letta_memory import LettaMemoryTool

load_dotenv()

book_web_search = create_book_web_search_tool()
create_prompt = create_veo3_prompt_tool()
letta_memory = LettaMemoryTool()

gemini_llm = LLM(
    model=os.getenv("YOUR_MODEL_ID"),
    api_key=os.getenv("MODEL_API_KEY"), # ENTER YOUR API KEY, use anthropic? or create your free gemini key
    temperature=0.7,
)

COMMON_TOOL_RULES = (
    "Tool usage rules:\n"
    "- To recall personalized improvement guidance before starting work, call letta_memory with "
    "{operation: 'memory_fetch', agent_source: '<role>'} and read the returned brief advice. "
    "Incorporate it into this task.\n"
    "- After completing work, persist a concise summary of your key decisions and rationale via "
    "letta_memory with {operation: 'memory_store', agents_response: '<summary>', agent_source: '<role>'}.\n"
    "Keep summaries short and structured so memory remains high-signal."
)

book_specialist = Agent(
    role="Book Research Specialist & Initial Script Creator",
    goal="Conduct comprehensive research for the target book and draft an initial 16s trailer framework without spoilers",
    backstory=(
        "A literary research expert for book marketing and trailer creation. "
        "Finds genre, author background, themes, hooks, cover visuals, quotes, pivotal scenes (no spoilers), "
        "and drafts a 5-6-5 initial trailer script. Stores findings for downstream agents.\n\n"
        + COMMON_TOOL_RULES
    ),
    tools=[book_web_search, letta_memory],
    llm=gemini_llm,
    verbose=True,
)

creative_dir = Agent(
    role="Creative Director & Script Architect",
    goal="Polish the 16s trailer script with strong emotional hooks and a clear 5-6-5 structure",
    backstory=(
        "A seasoned creative director for micro-content. Masters the 5-6-5 structure "
        "(5s hook, 6s development, 5s CTA+cover reveal). Documents key creative decisions.\n\n"
        + COMMON_TOOL_RULES
    ),
    tools=[letta_memory],
    llm=gemini_llm,
    verbose=True,
)

producer = Agent(
    role="Video Production Specialist & Prompt Engineer",
    goal="Translate the refined script into detailed, Veo3-optimized prompts with visual consistency",
    backstory=(
        "Bridges creative and production. Crafts prompts that specify composition, lighting, palette, "
        "camera moves, transitions, overlays, and book cover integration. Documents production decisions.\n\n"
        + COMMON_TOOL_RULES
    ),
    tools=[create_prompt, letta_memory],
    llm=gemini_llm,
    verbose=True,
)

feedback = Agent(
    role="User Experience Analyst & Feedback Coordinator",
    goal="Present Veo3 prompts, collect concise human feedback (2–3 follow-ups), analyze insights, and recommend improvements",
    backstory=(
        "Closes the feedback loop. Asks targeted questions, analyzes explicit/implicit signals, "
        "and produces actionable recommendations, storing results for future iterations.\n\n"
        "Tool usage rules:\n"
        "- Do NOT fetch at the start. After analyzing the human responses, persist a concise feedback summary via "
        "letta_memory with {operation: 'memory_store', agents_response: '<summary>', agent_source: 'feedback'}."
    ),
    tools=[letta_memory],
    llm=gemini_llm,
    verbose=True,
)

task1 = Task(
    description=(
        "First step: fetch personalized guidance for this role via letta_memory "
        "(operation='memory_fetch', agent_source='book_specialist') and briefly summarize how it will influence this task.\n"
        "Then conduct comprehensive research on '{book_title}'. "
        "Gather: genre/subgenre, author background & style, central themes, narrative hooks, "
        "cover/visual branding, notable quotes, pivotal scenes (no spoilers), target audience & positioning. "
        "Create an initial 16-second 5-6-5 trailer framework.\n"
        "Finally, store a concise summary of your key decisions and rationale via letta_memory "
        "(operation='memory_store', agent_source='book_specialist')."
    ),
    expected_output=(
        "JSON with:\n"
        "- fetched_guidance: '<short summary of memory_fetch advice>'\n"
        "- research: {genre, subgenre, author, themes, hooks, cover_visuals, quotes, pivotal_scenes_no_spoilers, audience, positioning}\n"
        "- initial_script_16s: {hook_5s, develop_6s, close_5s}\n"
        "- memory_note: 'Stored concise summary to memory'\n"
    ),
    agent=book_specialist,
)

task2 = Task(
    description=(
        "First step: fetch personalized guidance via letta_memory "
        "(operation='memory_fetch', agent_source='creative_dir') and briefly summarize how it will influence this task.\n"
        "Refine the raw script from the research step into a polished, production-ready 16s trailer (5-6-5). "
        "Optimize hook, emotional resonance, tone by genre, CTA, and cover reveal while maintaining mystery. "
        "Document the 5 most important creative decisions with rationale.\n"
        "Finally, store those decisions via letta_memory "
        "(operation='memory_store', agent_source='creative_dir')."
    ),
    expected_output=(
        "JSON with:\n"
        "- fetched_guidance: '<short summary of memory_fetch advice>'\n"
        "- final_script_16s: {\n"
        "    hook_5s: '<exact text for first 5s>',\n"
        "    develop_6s: '<exact text for middle 6s>',\n"
        "    close_5s: '<exact text for final 5s + CTA/cover reveal>',\n"
        "    timing_notes: '<beats or seconds mapping>'\n"
        "  }\n"
        "- creative_decisions: [5 items]\n"
        "- memory_note: 'Stored creative decisions to memory'\n"
    ),
    agent=creative_dir,
    context=[task1],
)

task3 = Task(
    description=(
        "First step: fetch personalized guidance via letta_memory "
        "(operation='memory_fetch', agent_source='producer') and briefly summarize how it will influence this task.\n"
        "You MUST use the 'final_script_16s' from the previous task's output as the sole narrative source. "
        "Do not invent or assume missing content. If 'final_script_16s' is missing, stop and return an explicit error "
        "message instructing to rerun Task 2.\n\n"
        "Transform that refined script into Veo3-optimized prompts:\n"
        "- For each segment (hook_5s, develop_6s, close_5s), create a precise Veo3 prompt that reflects the script's text and tone.\n"
        "- Specify scene composition & framing, lighting & mood, color palette, camera angles & moves, transitions, "
        "VFX/style, text overlays with timing, and book cover integration.\n"
        "- Define global consistency rules so the three clips feel unified.\n\n"
        "After producing the prompts, store a concise production summary via letta_memory "
        "(operation='memory_store', agent_source='producer')."
    ),
    expected_output=(
        "JSON with:\n"
        "- fetched_guidance: '<short summary of memory_fetch advice>'\n"
        "- script_used: {\n"
        "    hook_5s: '<copied from final_script_16s>',\n"
        "    develop_6s: '<copied from final_script_16s>',\n"
        "    close_5s: '<copied from final_script_16s>'\n"
        "  }\n"
        "- veo3_prompts: [\n"
        "    {segment: 'hook', prompt: '...'},\n"
        "    {segment: 'develop', prompt: '...'},\n"
        "    {segment: 'close', prompt: '...'}\n"
        "  ]\n"
        "- production_decisions: [5 items]\n"
        "- memory_note: 'Stored production summary to memory'\n"
    ),
    agent=producer,
    context=[task2],
)


task4 = Task(
    description=(
        "Present the generated Veo3 prompts (veo3_prompts) from prior outputs to the human. "
        "Ask exactly 2–3 concise follow-ups:\n"
        "- Does the hook feel intriguing and on-genre?\n"
        "- Is the tone/visual mood aligned with expectations?\n"
        "- What is the single most important improvement?\n"
        "After collecting responses, analyze them for themes and sentiment, and produce prioritized recommendations. "
        "Finally, store a concise feedback summary in memory via letta_memory "
        "(operation='memory_store', agent_source='feedback')."
    ),
    expected_output=(
        "JSON with:\n"
        "- presented_prompts: veo3_prompts (echoed)\n"
        "- collected_feedback: {answers, notable_phrases}\n"
        "- analysis: {themes, sentiment, priorities}\n"
        "- recommendations: [ranked actionable changes]\n"
        "- memory_note: 'Stored feedback summary to memory'\n"
    ),
    agent=feedback,
    human_input=True,
)

crew = Crew(
    agents=[book_specialist, creative_dir, producer, feedback],
    tasks=[task1, task2, task3, task4],
    process=Process.sequential,
    verbose=True,
    memory=False,
)

if __name__ == "__main__":
    result = crew.kickoff(inputs={"book_title": "Dune"})
    print("######################")
    print(result)
