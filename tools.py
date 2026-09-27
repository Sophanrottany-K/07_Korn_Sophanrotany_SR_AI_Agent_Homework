from schemas import (
    SearchProductsInput,
    CheckStockInput,
    BuyProductInput,
    EditProductInput,
    DeleteProductInput,
)

PRODUCTS = [
    {"id": 1, "name": "Dell Laptop", "category": "laptop", "price": 800, "stock": 5},
    {"id": 2, "name": "HP Laptop", "category": "laptop", "price": 700, "stock": 0},
    {"id": 3, "name": "iPhone 15", "category": "phone", "price": 900, "stock": 10},
    {"id": 4, "name": "Samsung Galaxy S24", "category": "phone", "price": 850, "stock": 3},
]


def search_products(query: str):
    data = SearchProductsInput(query=query)
    q = data.query.strip().lower()

    results = [
        {
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "price": p["price"],
        }
        for p in PRODUCTS
        if q in p["name"].lower() or q in p["category"].lower()
    ]

    return {"products": results}


def check_stock(product_id: int):
    data = CheckStockInput(product_id=product_id)

    product = next((p for p in PRODUCTS if p["id"] == data.product_id), None)
    if product is None:
        return {"error": "PRODUCT_NOT_FOUND", "message": "Product does not exist."}

    return {
        "product_id": product["id"],
        "name": product["name"],
        "stock": product["stock"],
        "available": product["stock"] > 0,
    }


def buy_product(product_id: int, quantity: int):
    data = BuyProductInput(product_id=product_id, quantity=quantity)

    product = next((p for p in PRODUCTS if p["id"] == data.product_id), None)
    if product is None:
        return {"error": "PRODUCT_NOT_FOUND", "message": "Product does not exist."}

    if product["stock"] < data.quantity:
        return {
            "error": "OUT_OF_STOCK",
            "message": f"Only {product['stock']} unit(s) are available."
        }

    product["stock"] -= data.quantity

    return {
        "success": True,
        "product_id": product["id"],
        "name": product["name"],
        "quantity": data.quantity,
        "remaining_stock": product["stock"],
    }
def edit_product(
    product_id: int,
    name: str | None = None,
    category: str | None = None,
    price: float | None = None,
    stock: int | None = None,
):
    data = EditProductInput(
        product_id=product_id,
        name=name,
        category=category,
        price=price,
        stock=stock,
    )

    if not data.has_update():
        return {
            "error": "NO_CHANGES",
            "message": "At least one field must be provided."
        }

    product = next(
        (p for p in PRODUCTS if p["id"] == data.product_id),
        None
    )

    if product is None:
        return {
            "error": "PRODUCT_NOT_FOUND",
            "message": "Product does not exist."
        }

    if data.name is not None:
        product["name"] = data.name

    if data.category is not None:
        product["category"] = data.category

    if data.price is not None:
        product["price"] = data.price

    if data.stock is not None:
        product["stock"] = data.stock

    return {
        "success": True,
        "message": "Product updated successfully.",
        "product": product.copy()
    }


def delete_product(product_id: int):
    data = DeleteProductInput(product_id=product_id)

    product = next(
        (p for p in PRODUCTS if p["id"] == data.product_id),
        None
    )

    if product is None:
        return {
            "error": "PRODUCT_NOT_FOUND",
            "message": "Product does not exist."
        }

    PRODUCTS.remove(product)

    return {
        "success": True,
        "message": "Product deleted successfully.",
        "deleted_product": product
    }