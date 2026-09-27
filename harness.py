from pydantic import ValidationError

from schemas import (
    SearchProductsInput,
    CheckStockInput,
    BuyProductInput,
    EditProductInput,
    DeleteProductInput,
)

from tools import (
    search_products,
    check_stock,
    buy_product,
    edit_product,
    delete_product,
)


# Maximum number of tool calls allowed in one agent run.
MAX_TOOL_CALLS = 5


# ============================================================
# PERMISSION CONTROL
# ============================================================

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


# ============================================================
# TOOL SCHEMAS
# ============================================================

SCHEMAS = {
    "search_products": SearchProductsInput,
    "check_stock": CheckStockInput,
    "buy_product": BuyProductInput,
    "edit_product": EditProductInput,
    "delete_product": DeleteProductInput,
}


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

IMPLEMENTATIONS = {
    "search_products": search_products,
    "check_stock": check_stock,
    "buy_product": buy_product,
    "edit_product": edit_product,
    "delete_product": delete_product,
}


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_tool(tool_name: str, arguments: dict, role: str):

    # --------------------------------------------------------
    # 1. Check whether the requested tool exists
    # --------------------------------------------------------

    if tool_name not in IMPLEMENTATIONS:
        return {
            "error": "TOOL_NOT_ALLOWED",
            "message": f"Unknown tool: {tool_name}",
        }


    # --------------------------------------------------------
    # 2. Check user permission
    # --------------------------------------------------------

    allowed_tools = PERMISSIONS.get(role, set())

    if tool_name not in allowed_tools:
        return {
            "error": "PERMISSION_DENIED",
            "message": (
                f"Role '{role}' does not have permission "
                f"to execute '{tool_name}'."
            ),
        }


    # --------------------------------------------------------
    # 3. Validate tool arguments
    # --------------------------------------------------------

    schema = SCHEMAS[tool_name]

    try:
        validated_arguments = schema(**arguments)

    except ValidationError as exc:
        return {
            "error": "INVALID_INPUT",
            "message": "Tool arguments failed validation.",
            "details": exc.errors(),
        }


    # --------------------------------------------------------
    # 4. Execute the actual tool
    # --------------------------------------------------------

    try:
        result = IMPLEMENTATIONS[tool_name](
            **validated_arguments.model_dump(exclude_none=True)
        )

        return result

    except Exception:
        # Never expose raw application exceptions
        # to the agent/user.
        return {
            "error": "TOOL_EXECUTION_ERROR",
            "message": "The tool could not complete the operation.",
        }