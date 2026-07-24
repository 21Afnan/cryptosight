from fastapi import APIRouter
from cryptosight.backend.services.dashboard_service import get_dashboard_summary

router = APIRouter()

@router.get("/summary")
def dashboard_summary():
    return get_dashboard_summary()
