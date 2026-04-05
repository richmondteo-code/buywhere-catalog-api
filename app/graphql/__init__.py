import asyncio
from concurrent.futures import ThreadPoolExecutor
from ariadne import graphql_sync
from ariadne.explorer import ExplorerGraphiQL
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse

from app.database import get_sync_db
from app.graphql.resolvers import schema

explorer_html = ExplorerGraphiQL().html(None)

graphql_router = APIRouter()

_executor = ThreadPoolExecutor(max_workers=10)


@graphql_router.get("/graphql", include_in_schema=False)
async def graphql_playground() -> HTMLResponse:
    return HTMLResponse(content=explorer_html)


@graphql_router.post("/graphql", include_in_schema=False)
async def graphql_endpoint(request: Request) -> JSONResponse:
    data = await request.json()
    db = get_sync_db()
    try:
        loop = asyncio.get_event_loop()
        success, result = await loop.run_in_executor(
            _executor,
            lambda: graphql_sync(
                schema,
                data,
                context_value={"request": request, "db": db},
                debug=False,
            )
        )
    finally:
        db.close()
    status_code = 200 if success else 400
    return JSONResponse(content=result, status_code=status_code)
