from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import Settings
from bot.keyboards.main import back_menu_kb, main_menu_kb
from bot.services.respond import send_banner
from bot.services.storage import Storage
from bot.states.deal import RequisitesStates

router = Router()


@router.callback_query(F.data == "req:ton")
async def ask_ton_wallet(cb: CallbackQuery, state: FSMContext, settings: Settings, storage: Storage) -> None:
    await state.set_state(RequisitesStates.waiting_ton)
    lang = await storage.get_user_language(cb.from_user.id)
    await send_banner(
        cb.message,
        settings,
        "<b>🔑 Добавьте ваш TON-кошелек:</b>\n\n<b>Пожалуйста, отправьте адрес вашего кошелька.</b>",
        reply_markup=back_menu_kb(lang),
    )
    await cb.answer()


@router.callback_query(F.data == "req:card")
async def ask_card(cb: CallbackQuery, state: FSMContext, settings: Settings, storage: Storage) -> None:
    await state.set_state(RequisitesStates.waiting_card)
    lang = await storage.get_user_language(cb.from_user.id)
    await send_banner(
        cb.message,
        settings,
        "<b>💳 ВВОД РЕКВИЗИТОВ КАРТЫ</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>⚠️ ВНИМАНИЕ: Обязательно укажите правильный номер карты!</b>\n"
        "<b>Бот будет автоматически переводить деньги именно на эти реквизиты.</b>\n\n"
        "<b>Пожалуйста, отправьте номер вашей карты (16-19 цифр) и название банка.</b>\n"
        "<b>Пример: Sberbank - 4444 4444 4444 4444</b>",
        reply_markup=back_menu_kb(lang),
    )
    await cb.answer()


@router.message(RequisitesStates.waiting_ton)
async def save_ton_wallet(message: Message, state: FSMContext, settings: Settings, storage: Storage) -> None:
    lang = await storage.get_user_language(message.from_user.id)
    wallet = (message.text or "").strip()
    if len(wallet) < 8:
        await send_banner(message, settings, "<b>Неверный адрес TON-кошелька. Попробуйте снова.</b>")
        return

    await storage.set_payment_method(message.from_user.id, "ton", wallet)
    await state.clear()
    
    await send_banner(
        message,
        settings,
        "<b>✅ TON-кошелек успешно добавлен/изменен!</b>",
        reply_markup=main_menu_kb(lang, is_admin=message.from_user.id == settings.owner_id),
    )


@router.message(RequisitesStates.waiting_card)
async def save_card(message: Message, state: FSMContext, settings: Settings, storage: Storage) -> None:
    lang = await storage.get_user_language(message.from_user.id)
    card = (message.text or "").strip()
    
    # Simple validation for card-like numbers
    digits_only = "".join(filter(str.isdigit, card))
    if len(digits_only) < 16:
        await send_banner(
            message, 
            settings, 
            "<b>❌ ОШИБКА: Номер карты слишком короткий!</b>\n"
            "<b>Пожалуйста, перепроверьте и введите полный номер карты (16 цифр).</b>"
        )
        return

    await storage.set_payment_method(message.from_user.id, "card", card)
    await state.clear()
    
    await send_banner(
        message,
        settings,
        "<b>✅ РЕКВИЗИТЫ УСПЕШНО СОХРАНЕНЫ!</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>Ваши данные:</b> <code>{card}</code>\n\n"
        "<b>⚠️ ПЕРЕПРОВЕРЬТЕ ЕЩЕ РАЗ! Если номер неверный, деньги уйдут в никуда.</b>",
        reply_markup=main_menu_kb(lang, is_admin=message.from_user.id == settings.owner_id),
    )

