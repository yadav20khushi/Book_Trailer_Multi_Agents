import os
from typing import Type
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from letta_client import Letta, MessageCreate, TextContent

load_dotenv()


class MyToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    agent_ques: str = Field(description="question asked by the test_agent")


class LettaTestTool(BaseTool):
    name: str = "letta_test"
    description: str = "test connection with the letta"
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, agent_ques: str) -> str:
        try:
            LETTA_PROJECT: str = os.getenv("LETTA_PROJECT", "")
            LETTA_API_KEY: str = os.getenv("LETTA_API_KEY", "")
            AGENT_ID: str = os.getenv("AGENT_ID", "")

            client = Letta(
                project=LETTA_PROJECT,
                token=LETTA_API_KEY
            )

            response = client.agents.messages.create(
                agent_id=AGENT_ID,
                messages=[MessageCreate(
                    role="user",
                    content=[TextContent(text=agent_ques)],
                )],
                max_steps=1,
                include_return_message_types=["assistant_message"]
            )

            if hasattr(response, "messages") and response.messages:
                assistant_message = response.messages[0]
                if hasattr(assistant_message, "content"):
                    if isinstance(assistant_message.content, str):
                        raw_reply = assistant_message.content
                    elif isinstance(assistant_message.content, list):
                        raw_reply = " ".join([c.text for c in assistant_message.content if hasattr(c, "text")])
                    else:
                        raw_reply = "No content in response"
                    return f"Letta Response: {raw_reply}"

            return "No response from Letta"

        except Exception as e:
            return f"Error connecting to Letta: {str(e)}"


# Create tool instance
letta_test = LettaTestTool()

gemini_llm = LLM(
    model=os.getenv("GEMINI_MODEL_ID"),
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7,
)

test_agent = Agent(
    role="test connection with letta",
    goal="To connect with letta and ask a question and wait for its response",
    backstory="You seamlessly connect with letta",
    tools=[letta_test],
    llm=gemini_llm,
    verbose=True,
)

task1 = Task(
    description="Ask letta to give its introduction",
    expected_output="An introduction of letta",
    agent=test_agent,
)


crew = Crew(
    agents=[test_agent],
    tasks=[task1],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("######################")
    print(result)