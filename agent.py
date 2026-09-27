import json
import os
from typing import Any

from harness import MAX_TOOL_CALLS, execute_tool

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


SYSTEM_PROMPT = """
You are a simple shopping agent.

Your job is to help the user using the available tools.

Available tools:
1. search_products(query)
2. check_stock(product_id)
3. buy_product(product_id, quantity)
4. edit_product(product_id, name?, category?, price?, stock?)
5. delete_product(product_id)

Rules:
- Decide when a tool is needed.
- Use tool results to decide what to do next.
- Never invent product IDs, stock values, or purchase results.
- If a tool returns an error, explain it clearly.
- Keep answers concise.
- Do not claim that an action happened unless the tool result confirms it.
- The application enforces permissions; do not try to bypass them.
"""


def get_client():
    if OpenAI is None:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt")

    # Default: Ollama's OpenAI-compatible local endpoint.
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    api_key = os.getenv("LLM_API_KEY", "ollama")
    model = os.getenv("LLM_MODEL", "qwen3:4b")

    client = OpenAI(base_url=base_url, api_key=api_key)
    return client, model


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search products by name or category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Product name or category"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check current stock for a product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Positive product ID"}
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buy_product",
            "description": "Buy a quantity of a product. The application decides whether the user's role has permission.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Positive product ID"},
                    "quantity": {"type": "integer", "description": "Quantity from 1 to 100"},
                },
                "required": ["product_id", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_product",
            "description": "Edit an existing product. Admin only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Product ID"
                    },
                    "name": {
                        "type": "string",
                        "description": "New product name"
                    },
                    "category": {
                        "type": "string",
                        "description": "New product category"
                    },
                    "price": {
                        "type": "number",
                        "description": "New product price"
                    },
                    "stock": {
                        "type": "integer",
                        "description": "New stock quantity"
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_product",
            "description": "Delete an existing product. Admin only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Product ID"
                    }
                },
                "required": ["product_id"]
            }
        }
    }
]


def run_agent(user_request: str, role: str) -> dict[str, Any]:
    client, model = get_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"User role: {role}\nRequest: {user_request}",
        },
    ]

    trace = []

    for iteration in range(1, MAX_TOOL_CALLS + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return {
                "answer": message.content or "I could not produce an answer.",
                "trace": trace,
            }

        messages.append(message)

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name

            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                result = {
                    "error": "INVALID_TOOL_ARGUMENTS",
                    "message": "The model produced invalid JSON arguments.",
                }
                arguments = {}
            else:
                result = execute_tool(tool_name, arguments, role)

            trace.append(
                f"Iteration {iteration}: {tool_name}({arguments}) -> {result}"
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

    return {
        "answer": "The agent stopped because the maximum tool-call limit was reached.",
        "trace": trace,
    }
