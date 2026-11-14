from pydantic import BaseModel, ConfigDict


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution: str
    card_name: str | None  # 화면에 보여줄 별칭 (없으면 기관명 + 마스킹 번호)
    card_number_masked: str | None
    card_type: str | None
    is_active: bool


class CardUpdate(BaseModel):
    card_name: str | None = None
