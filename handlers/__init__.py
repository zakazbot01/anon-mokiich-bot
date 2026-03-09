from aiogram import Dispatcher
from .start import router as start_router
from .question import router as question_router
from .payment import router as payment_router
from .reply import router as reply_router

def register_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(question_router)
    dp.include_router(payment_router)
    dp.include_router(reply_router)
