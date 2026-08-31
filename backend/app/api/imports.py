from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.import_result import ImportResultOut
from app.services.import_service import NoMatchingImporterError, import_file

router = APIRouter(tags=["import"])


def _save_upload(file: UploadFile) -> Path:
    settings.imports_path.mkdir(parents=True, exist_ok=True)
    # Strip any directory components the client might send - only the
    # basename is trusted, and it's written under imports/ only.
    safe_name = Path(file.filename or "upload").name
    dest = settings.imports_path / safe_name

    counter = 1
    stem, suffix = dest.stem, dest.suffix
    while dest.exists():
        dest = settings.imports_path / f"{stem}_{counter}{suffix}"
        counter += 1

    with dest.open("wb") as out:
        out.write(file.file.read())
    return dest


@router.post("/import", response_model=ImportResultOut)
def upload_and_import(
    file: UploadFile,
    preview: bool = Query(default=False, description="true면 DB에 반영하지 않고 미리보기만 계산"),
    db: Session = Depends(get_db),
):
    dest = _save_upload(file)
    try:
        result = import_file(dest, db, dry_run=preview)
    except NoMatchingImporterError as exc:
        if preview:
            dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if preview:
        # The uploaded file itself only needs to stick around for a real
        # import - a preview shouldn't leave stray files in imports/.
        dest.unlink(missing_ok=True)

    return result
