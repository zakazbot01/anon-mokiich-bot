from aiogram.fsm.state import State, StatesGroup


class CreateLink(StatesGroup):
    choose_destination = State()
    enter_channel = State()
    choose_reveal = State()
    confirm = State()


class AskQuestion(StatesGroup):           # ← новое состояние для анонимных вопросов
    waiting_for_question = State()
