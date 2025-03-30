from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from api.database.search_dao import SearchDAO
from api.database.database import get_db
from api.models.search import SearchRequest, SearchResponse
from api.common.decorators import handle_db_errors, log_request

router = APIRouter()
search_dao = SearchDAO()

@router.post("/search", response_model=SearchResponse)
@handle_db_errors
@log_request
async def agent_search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    return await search_dao.search_contents(db, request)

@router.get("/search/suggest")
async def get_search_suggestions(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    return await search_dao.get_suggestions(db, q) 