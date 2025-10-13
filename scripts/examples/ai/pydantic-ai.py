# fasthtml solveit
from pylogue.chatapp import create_default_chat_app
import logfire
from pydantic_ai import Agent

logfire.configure(token="your-token-here")
logfire.instrument_pydantic_ai()

agent = Agent(
    "google-gla:gemini-2.5-flash",
    system_prompt="You are a stoic and usually talk as less as possible.",
)


class PydanticAIAgentResponder:
    def __init__(self, agent=None, agent_deps=None):
        self.agent = agent if agent is not None else self.init_agent()
        self.agent_deps = agent_deps

    async def __call__(self, text: str, context=None) -> str:
        response = await self.agent.run(
            text,
            message_history=(
                self.message_history if hasattr(self, "message_history") else None
            ),
            deps=self.agent_deps,
        )
        self.message_history = response.all_messages()
        return response.output


if __name__ == "__main__":
    # Create with one line
    responder = PydanticAIAgentResponder(agent=agent)
    app = create_default_chat_app(responder=responder)
    app.run(port=5001)
