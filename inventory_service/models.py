from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    sku: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
