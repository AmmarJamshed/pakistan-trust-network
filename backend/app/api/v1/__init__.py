from fastapi import APIRouter

from app.api.v1 import auth, credentials, cv, ledger, organizations, public_verify, stats, wallet

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(credentials.router)
api_router.include_router(public_verify.router)
api_router.include_router(ledger.router)
api_router.include_router(wallet.router)
api_router.include_router(cv.router)
api_router.include_router(stats.router)
api_router.include_router(stats.admin_router)

# Compatibility aliases matching the spec
# GET /api/users/{id}/wallet is covered via /api/wallet/users/{id}
# POST /api/identities via /api/organizations/{id}/identity
