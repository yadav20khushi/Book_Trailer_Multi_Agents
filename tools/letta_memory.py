import os
from typing import Optional, Type, List
from dotenv import load_dotenv
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, validator

from letta_client import Letta, MessageCreate, TextContent

load_dotenv()

class LettaMemoryInput(BaseModel):
    operation: str = Field(
        description="Operation to perform: 'memory_fetch' or 'memory_store'"
    )
    agents_response: Optional[str] = Field(
        default=None,
        description="For 'memory_store': key decisions and brief summary of user feedback. For 'memory_fetch': may be omitted."
    )
    agent_source: Optional[str] = Field(
        default="crew",
        description="Optional source tag for auditing (e.g., 'book_specialist' | 'creative_dir' | 'producer' | 'feedback')."
    )

    @validator("operation")
    def validate_operation(cls, v: str) -> str:
        allowed = {"memory_fetch", "memory_store"}
        if v not in allowed:
            raise ValueError(f"operation must be one of {allowed}")
        return v

    @validator("agents_response", always=True)
    def validate_agents_response(cls, v: Optional[str], values):
        op = values.get("operation")
        if op == "memory_store" and (v is None or not v.strip()):
            raise ValueError("agents_response is required for operation 'memory_store'")
        return v

class LettaMemoryTool(BaseTool):
    name: str = "letta_memory"
    description: str = (
        "Store or fetch iterative project memory in Letta. "
        "Use operation='memory_store' to persist concise decisions/feedback; "
        "use operation='memory_fetch' to retrieve prior context."
    )
    args_schema: Type[BaseModel] = LettaMemoryInput
    return_direct: bool = False

    def letta_connect(self, text: str) -> str:
        try:
            LETTA_PROJECT: str = os.getenv("LETTA_PROJECT", "").strip()
            LETTA_API_KEY: str = os.getenv("LETTA_API_KEY", "").strip()
            AGENT_ID: str = os.getenv("AGENT_ID", "").strip()

            if not LETTA_API_KEY:
                return "Letta error: missing LETTA_API_KEY in environment"
            if not AGENT_ID:
                return "Letta error: missing AGENT_ID in environment"

            client = Letta(
                token=LETTA_API_KEY,
                project=LETTA_PROJECT if LETTA_PROJECT else None,
            )

            response = client.agents.messages.create(
                agent_id=AGENT_ID,
                messages=[
                    MessageCreate(
                        role="user",
                        content=[TextContent(text=text)],
                    )
                ],
                max_steps=1,
                include_return_message_types=["assistant_message"],
            )

        except Exception as e:
            return f"Letta error: {str(e)}"

        try:
            if hasattr(response, "messages") and response.messages:
                assistant_message = response.messages[0]
                content = assistant_message.content
                if isinstance(content, str):
                    raw_reply = content
                elif isinstance(content, list):
                    parts: List[str] = []
                    for c in content:
                        if hasattr(c, "text"):
                            parts.append(c.text)
                        elif isinstance(c, dict) and "text" in c:
                            parts.append(str(c["text"]))
                        else:
                            parts.append(str(c))
                    raw_reply = " ".join(parts).strip()
                else:
                    raw_reply = str(content)
                return f"Letta Response: {raw_reply}" if raw_reply else "Letta Response: (empty)"
        except Exception as e:
            return f"Letta parse error: {str(e)}"

        return "Letta: No response messages returned"

    def memory_store(self, agents_response: str, agent_source: Optional[str] = "crew") -> str:
        payload = (
            f"[memory_store]"
            f"\nsource: {agent_source}"
            f"\nsummary: {agents_response.strip()}"
        )
        return self.letta_connect(payload)

    def memory_fetch(self, agent_source: Optional[str] = "crew") -> str:
        query = (
            f"[memory_fetch]"
            f"\nsource: {agent_source}"
            f"\nrequest: Provide the latest stored decisions and the latest brief user feedback summary. "
            f"If nothing exists yet, say 'no feedback yet'."
        )
        return self.letta_connect(query)

    def _run(
        self,
        operation: str,
        agents_response: Optional[str] = None,
        agent_source: Optional[str] = "crew",
    ) -> str:
        if operation == "memory_store":
            return self.memory_store(agents_response=agents_response or "", agent_source=agent_source)
        if operation == "memory_fetch":
            return self.memory_fetch(agent_source=agent_source)
        return "Unknown operation. Use 'memory_store' or 'memory_fetch'."


