from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import os
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(
    command="npx",
    args=["-y", "@zenrows/mcp"],
    env=dict(os.environ),
)
MODEL = "qwen3:latest"
# give the model enough context to read the whole tool result
OPTIONS = {"num_ctx": 16384}
QUESTION = "List the company names and job titles from https://www.indeed.com/jobs?q=data+analyst&l=Austin%2C+TX."
ALLOWED_ARGS = {"url"}

async def main():
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            listed = await session.list_tools()
            tools = [
                {"type": "function", "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema,
                }}
                for t in listed.tools if t.name == "extract"
            ]

            messages = [{"role": "user", "content": QUESTION}]
            reply = ollama.chat(model=MODEL, messages=messages, tools=tools, options=OPTIONS)
            messages.append(reply["message"])

            for call in reply["message"].get("tool_calls") or []:
                args = {k: v for k, v in call.function.arguments.items() if k in ALLOWED_ARGS}
                print("calling", call.function.name, args)
                result = await session.call_tool(call.function.name, args)
                text = result.content[0].text
                print("result:", text[:300])
                # pass the model only the parsed fields from the response
                data = json.loads(text).get("data")
                messages.append({"role": "tool", "content": json.dumps(data)})

            print(ollama.chat(model=MODEL, messages=messages, tools=tools, options=OPTIONS)["message"]["content"])

asyncio.run(main())
