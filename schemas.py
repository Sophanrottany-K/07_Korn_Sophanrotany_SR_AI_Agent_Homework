from typing import Literal
from pydantic import BaseModel, Field


class SearchProductsInput(BaseModel):
    query: str = Field(min_length=1, description="Product name or category to search for")


class CheckStockInput(BaseModel):
    product_id: int = Field(gt=0, description="Positive product ID")


class BuyProductInput(BaseModel):
    product_id: int = Field(gt=0, description="Positive product ID")
    quantity: int = Field(gt=0, le=100, description="Quantity from 1 to 100")


class ToolCall(BaseModel):
    tool_name: Literal["search_products", "check_stock", "buy_product"]
    arguments: dict

class EditProductInput(BaseModel):
    product_id: int = Field(gt=0)
    name: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1)
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)

    def has_update(self):
        return any([
            self.name is not None,
            self.category is not None,
            self.price is not None,
            self.stock is not None,
        ])


class DeleteProductInput(BaseModel):
    product_id: int = Field(gt=0)
