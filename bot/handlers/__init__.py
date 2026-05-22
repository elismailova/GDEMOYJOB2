from aiogram import Router
from .start import router as start_router
from .resume import router as resume_router
from .search import router as search_router

main_router = Router()
main_router.include_router(start_router)
main_router.include_router(resume_router)
main_router.include_router(search_router)

__all__ = ["main_router"]
