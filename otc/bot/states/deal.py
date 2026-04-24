from aiogram.fsm.state import State, StatesGroup


class RequisitesStates(StatesGroup):
    waiting_ton = State()
    waiting_card = State()


class DealStates(StatesGroup):
    waiting_amount = State()
    choosing_currency = State()
    waiting_description = State()


class AdminStates(StatesGroup):
    waiting_deal_lookup = State()
    waiting_broadcast_msg = State()
    waiting_topic_broadcast_msg = State()
