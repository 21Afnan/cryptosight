from fastapi import APIRouter, Query, HTTPException
from cryptosight.backend.services.wallet_service import get_wallets_data, add_wallet_account

router = APIRouter()


@router.api_route("", methods=["GET", "HEAD"], summary="Get Wallet Accounts & Equity Growth")
def get_wallets(
    search: str = Query("", description="Search term for exchange/account"),
    status: str = Query("", description="Filter by status (connected, disabled)"),
):
    """
    Returns live wallet account balances, API credentials status, assigned strategies,
    active positions, and equity growth curve from PostgreSQL.
    """
    try:
        return get_wallets_data(search=search, filter_status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", summary="Connect New Exchange Wallet")
def create_wallet(payload: dict):
    """
    Saves new exchange API credentials into PostgreSQL `account.api`.
    """
    try:
        return add_wallet_account(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
