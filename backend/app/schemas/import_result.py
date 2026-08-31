from pydantic import BaseModel


class ImportResultOut(BaseModel):
    source: str
    file_name: str
    batch_id: int | None
    total: int
    imported: int
    duplicates: int
    classified: int
    unclassified: int
