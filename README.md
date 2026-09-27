# Simple Safe Shopping Agent

## 1. Project Overview

**Simple Safe Shopping Agent** is a small tool-using AI agent for a shopping system.

The agent can understand a user's request, decide which tool to use, execute the tool through the application, observe the result, and then decide whether another tool call is needed or whether it can provide a final answer.

The agent follows this workflow:

```text
User Request
     ↓
Agent / LLM
     ↓
Tool Call
     ↓
Application Validation & Permission Check
     ↓
Tool Execution
     ↓
Tool Result
     ↓
Agent Observes Result
     ↓
Agent Decides Again ↺
     ↓
Final Answer
```

The project uses **Ollama** with an OpenAI-compatible API and can run a local model such as `qwen3:4b`.

---

## 2. Available Tools

The agent provides five tools.

| Tool | Description | Customer | Admin |
|---|---|:---:|:---:|
| `search_products` | Search products by name or category | ✅ | ✅ |
| `check_stock` | Check the current stock of a product | ✅ | ✅ |
| `buy_product` | Purchase a specified quantity of a product | ✅ | ✅ |
| `edit_product` | Modify product information | ❌ | ✅ |
| `delete_product` | Delete a product | ❌ | ✅ |

### 2.1 `search_products`

Searches products by product name or category.

Example:

```text
search_products(query="laptop")
```

### 2.2 `check_stock`

Checks whether a product is available and returns its current stock.

Example:

```text
check_stock(product_id=1)
```

### 2.3 `buy_product`

Purchases a product if enough stock is available.

Example:

```text
buy_product(product_id=1, quantity=2)
```

### 2.4 `edit_product`

Updates product information such as:

- name
- category
- price
- stock

This tool is available only to administrators.

Example:

```text
edit_product(
    product_id=1,
    price=750,
    stock=10
)
```

### 2.5 `delete_product`

Deletes a product from the product list.

This tool is available only to administrators.

Example:

```text
delete_product(product_id=4)
```

---

## 3. Agent Loop

The agent follows a repeated **decision → action → observation** loop.

```text
┌─────────────────┐
│   User Request  │
└────────┬────────┘
         ↓
┌─────────────────┐
│   Agent / LLM   │
│     Decision    │
└────────┬────────┘
         ↓
   Tool required?
      /      \
    Yes       No
     ↓         ↓
┌───────────┐  ┌─────────────┐
│ Tool Call │  │ Final Answer│
└─────┬─────┘  └─────────────┘
      ↓
┌──────────────────────┐
│ Application Harness  │
│ Permission + Schema  │
│ Validation           │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│    Tool Execution    │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│     Tool Result      │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Agent observes result│
└──────────┬───────────┘
           ↓
       Decide again ↺
```

For example, if the user asks:

```text
Find a laptop that is currently in stock.
```

The agent may first decide:

```text
search_products(query="laptop")
```

The tool returns matching products.

The agent observes the result and then decides which product should have its stock checked:

```text
check_stock(product_id=1)
```

The tool returns:

```json
{
    "product_id": 1,
    "name": "Dell Laptop",
    "stock": 5,
    "available": true
}
```

The agent observes this result and can then provide the final answer.

The important part of the agent loop is:

```text
User Request
     ↓
Agent Decision
     ↓
Tool Call
     ↓
Tool Result
     ↓
Agent Decision Again
     ↓
Final Answer
```

The result of one tool call can therefore influence the agent's next action.

---

## 4. Permission Rule

The application enforces permissions based on the user's role.

### Customer

A customer can use:

```text
search_products
check_stock
buy_product
```

A customer cannot use:

```text
edit_product
delete_product
```

### Admin

An administrator can use all five tools:

```text
search_products
check_stock
buy_product
edit_product
delete_product
```

The permission rule is enforced in **application code inside `harness.py`**.

```python
PERMISSIONS = {
    "customer": {
        "search_products",
        "check_stock",
        "buy_product",
    },
    "admin": {
        "search_products",
        "check_stock",
        "buy_product",
        "edit_product",
        "delete_product",
    },
}
```

Before a tool is executed, the harness checks whether the current role is allowed to use that tool.

For example, if a customer attempts:

```text
delete_product(product_id=4)
```

the application returns:

```json
{
    "error": "PERMISSION_DENIED",
    "message": "Role 'customer' does not have permission to execute 'delete_product'."
}
```

The delete operation is not executed.

---

## 5. Safety

The project includes several basic safety mechanisms.

### 5.1 Input Validation

Tool arguments are validated using **Pydantic schemas**.

For example:

```python
class CheckStockInput(BaseModel):
    product_id: int = Field(gt=0)
```

This requires `product_id` to be a positive integer.

The purchase quantity is also validated:

```python
class BuyProductInput(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)
```

Therefore, the purchase quantity must be between **1 and 100**.

### 5.2 Permission Validation

The application checks the user's role before executing a tool.

```text
User
  ↓
Agent requests tool
  ↓
Permission Check
  ↓
Allowed?
 ├── No  → PERMISSION_DENIED
 │
 └── Yes
       ↓
   Tool Execution
```

This means that permissions are enforced by the application rather than relying only on the LLM's instructions.

### 5.3 Error Handling

The application handles several types of errors.

| Error | Meaning |
|---|---|
| `PRODUCT_NOT_FOUND` | The requested product does not exist |
| `OUT_OF_STOCK` | There is not enough stock |
| `INVALID_INPUT` | Tool arguments failed validation |
| `PERMISSION_DENIED` | The user's role cannot execute the tool |
| `TOOL_EXECUTION_ERROR` | An unexpected tool execution error occurred |

The application catches tool execution exceptions and returns an error result instead of allowing the whole agent program to crash.

### 5.4 Maximum Tool-Call Limit

The agent has a maximum number of tool-call iterations:

```python
MAX_TOOL_CALLS = 5
```

This prevents the agent from continuing to call tools indefinitely.

```text
Iteration 1 → Tool Call
Iteration 2 → Tool Call
Iteration 3 → Tool Call
Iteration 4 → Tool Call
Iteration 5 → Tool Call
                 ↓
              Stop
```

If the maximum number of tool calls is reached, the agent stops and returns a message indicating that the maximum tool-call limit was reached.

---

## 6. Example Run

### Example 1: Customer Searches for an Available Laptop

The program starts:

```text
=== Simple Safe Shopping Agent ===
Type 'exit' to quit.

Role (customer/admin): customer

User request: Find a laptop that is currently in stock.
```

The agent decides to search for laptops:

```text
search_products({'query': 'laptop'})
```

The tool returns:

```json
{
    "products": [
        {
            "id": 1,
            "name": "Dell Laptop",
            "category": "laptop",
            "price": 800
        },
        {
            "id": 2,
            "name": "HP Laptop",
            "category": "laptop",
            "price": 700
        }
    ]
}
```

The agent observes the result and decides to check the stock of the Dell Laptop:

```text
check_stock({'product_id': 1})
```

The tool returns:

```json
{
    "product_id": 1,
    "name": "Dell Laptop",
    "stock": 5,
    "available": true
}
```

The agent then provides the final answer:

```text
Agent: The Dell Laptop is currently in stock.
There are 5 units available, priced at $800.
```

The complete agent flow is:

```text
User Request
     ↓
search_products
     ↓
Search Result
     ↓
Agent Observes Result
     ↓
check_stock
     ↓
Stock Result
     ↓
Agent Observes Result
     ↓
Final Answer
```

This demonstrates that the agent can **observe a tool result and use that result to decide its next action**.

### Example 2: Customer Attempts an Admin Action

Input:

```text
Role (customer/admin): customer

User request: Delete the Samsung Galaxy S24.
```

The agent requests:

```text
delete_product(product_id=4)
```

The application performs the permission check:

```text
Customer
   ↓
delete_product
   ↓
Permission Check
   ↓
Not Allowed
```

The tool is not executed.

The application returns:

```json
{
    "error": "PERMISSION_DENIED",
    "message": "Role 'customer' does not have permission to execute 'delete_product'."
}
```

The agent receives this result and can explain that the customer does not have permission to delete products.

---

## Project Structure

```text
simple-safe-agent/
│
├── main.py
├── agent.py
├── tools.py
├── schemas.py
├── harness.py
├── requirements.txt
├── README.md
└── .gitignore
```

### File Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | User input and program entry point |
| `agent.py` | LLM connection, tool selection, and agent loop |
| `tools.py` | Tool implementations and product data |
| `schemas.py` | Pydantic input schemas |
| `harness.py` | Permission checks, validation, tool execution, and error handling |
| `requirements.txt` | Python dependencies |
| `README.md` | Project documentation |

---

## Running the Project

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Make Sure Ollama Is Running

Download the model:

```bash
ollama pull qwen3:4b
```

Make sure the Ollama service is running.

### 3. Start the Agent

```bash
python main.py
```

### 4. Select a Role

For a customer:

```text
Role (customer/admin): customer
```

For an administrator:

```text
Role (customer/admin): admin
```

### 5. Enter a Request

For example:

```text
User request: Find a laptop that is currently in stock.
```

To stop the program:

```text
exit
```
