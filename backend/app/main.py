from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import cards, categories, category_rules, imports, stats, transactions

app = FastAPI(
    title="my-ledger API",
    description="개인용 로컬 가계부 API. 로컬 PC에서만 실행됩니다.",
)

app.include_router(transactions.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(category_rules.router, prefix="/api")
app.include_router(cards.router, prefix="/api")
app.include_router(imports.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


# In dev, the frontend runs on its own Vite server (npm run dev) and
# proxies /api/* here. In "single-process" mode, `npm run build` output
# is served directly by this same FastAPI process - no separate
# frontend server needed.
_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        # Client-side (React Router) paths all resolve to the SPA shell;
        # only /api/* and /assets/* are real backend routes.
        return FileResponse(_FRONTEND_DIST / "index.html")
