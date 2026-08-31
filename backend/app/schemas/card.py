from pydantic import BaseModel, ConfigDict


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution: str
    card_number_masked: str | None
    card_type: str | None
    is_active: bool
