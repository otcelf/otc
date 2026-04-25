from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import Settings
from bot.keyboards.main import admin_deal_actions_kb, admin_deals_page_kb, admin_panel_kb, main_menu_kb
from bot.services.respond import send_banner, send_banner_to_chat
from bot.services.storage import DealRecord, Storage
from bot.states.deal import AdminStates

router = Router()


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id == settings.owner_id


def _deal_line(deal: DealRecord) -> str:
    buyer = deal.buyer_id if deal.buyer_id else "—"
    return (
        f"<b>#{deal.id}</b> | <b>{deal.amount} {deal.currency}</b> | "
        f"<b>{deal.status}</b> | <b>seller:{deal.seller_id}</b> | <b>buyer:{buyer}</b>"
    )


def _deal_card(deal: DealRecord) -> str:
    buyer = deal.buyer_id if deal.buyer_id else "—"
    return (
        f"<b>🧾 Сделка #{deal.id}</b>\n\n"
        f"<b>Статус:</b> <b>{deal.status}</b>\n"
        f"<b>Сумма:</b> <b>{deal.amount} {deal.currency}</b>\n"
        f"<b>Тип выплаты:</b> <b>{deal.payout_type}</b>\n"
        f"<b>Продавец:</b> <b>{deal.seller_id}</b>\n"
        f"<b>Покупатель:</b> <b>{buyer}</b>\n"
        f"<b>Token:</b> <b>{deal.start_token}</b>\n"
        f"<b>Создана:</b> <b>{deal.created_at}</b>\n\n"
        f"<b>Описание:</b> <b>{deal.description}</b>"
    )


@router.message(CommandStart())
async def admin_start(message: Message, state: FSMContext, settings: Settings, storage: Storage) -> None:
    # This is just to satisfy any imports, but we already have start handler in start.py
    pass


@router.message(F.text == "/get_id")
async def get_chat_id(message: Message) -> None:
    text = (
        f"<b>🆔 Инфо о чате:</b>\n"
        f"<b>Chat ID:</b> <code>{message.chat.id}</code>\n"
        f"<b>Thread ID:</b> <code>{message.message_thread_id or 'Main'}</code>"
    )
    await message.answer(text)


@router.callback_query(F.data == "admin:panel")
async def admin_panel(cb: CallbackQuery, settings: Settings) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return
    
    # Force refresh the message to show new keyboard
    text = "<b>🛡 Админ-панель</b>\n\n<b>Управление проектом OTC.</b>"
    reply_markup = admin_panel_kb()
    
    try:
        await cb.message.edit_caption(caption=text, reply_markup=reply_markup)
    except Exception:
        await send_banner(cb.message, settings, text, reply_markup=reply_markup)
    await cb.answer()


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_prompt(cb: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_broadcast_msg)
    await send_banner(
        cb.message,
        settings,
        "<b>📢 Введите сообщение для рассылки всем пользователям.</b>\n\n<b>Поддерживается HTML разметка.</b>",
    )
    await cb.answer()


@router.message(AdminStates.waiting_broadcast_msg)
async def admin_broadcast_handle(message: Message, state: FSMContext, settings: Settings, storage: Storage) -> None:
    if not _is_admin(message.from_user.id, settings):
        await state.clear()
        return

    broadcast_text = message.html_text
    await state.clear()

    user_ids = await storage.get_all_telegram_ids()
    count = 0
    for uid in user_ids:
        try:
            await send_banner_to_chat(message.bot, settings, uid, broadcast_text)
            count += 1
        except Exception:
            continue

    await send_banner(
        message,
        settings,
        f"<b>✅ Рассылка завершена!</b>\n<b>Сообщение получили {count} пользователей.</b>",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "admin:broadcast_topic")
async def admin_broadcast_topic_prompt(cb: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_topic_broadcast_msg)
    await send_banner(
        cb.message,
        settings,
        "<b>💬 Введите сообщение для рассылки в ТОПИК приватного чата.</b>\n\n"
        "<b>Чат ID:</b> <code>-1003887218129</code>\n"
        "<b>Топик ID:</b> <code>2</code>",
    )
    await cb.answer()


@router.message(AdminStates.waiting_topic_broadcast_msg)
async def admin_broadcast_topic_handle(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await state.clear()
        return

    broadcast_text = message.html_text
    await state.clear()

    target_chat_id = -1003887218129
    target_thread_id = 2

    try:
        await send_banner_to_chat(
            message.bot, 
            settings, 
            target_chat_id, 
            broadcast_text, 
            message_thread_id=target_thread_id
        )
        await send_banner(
            message,
            settings,
            "<b>✅ Сообщение успешно отправлено в топик!</b>",
            reply_markup=admin_panel_kb(),
        )
    except Exception as e:
        await send_banner(
            message,
            settings,
            f"<b>❌ Ошибка при отправке:</b>\n<code>{str(e)}</code>",
            reply_markup=admin_panel_kb(),
        )


@router.callback_query(F.data == "admin:stats")
async def admin_stats(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return

    total = await storage.count_all_deals()
    users = await storage.count_users()
    completed = await storage.count_deals_by_status("completed")
    disputed = await storage.count_deals_by_status("disputed")
    created = await storage.count_deals_by_status("created")
    paid = await storage.count_deals_by_status("paid")
    buyer_joined = await storage.count_deals_by_status("buyer_joined")

    await send_banner(
        cb.message,
        settings,
        "<b>📊 Статистика</b>\n\n"
        f"<b>👥 Пользователей:</b> <b>{users}</b>\n"
        f"<b>🧾 Всего сделок:</b> <b>{total}</b>\n"
        f"<b>🕒 created:</b> <b>{created}</b>\n"
        f"<b>🤝 buyer_joined:</b> <b>{buyer_joined}</b>\n"
        f"<b>💸 paid:</b> <b>{paid}</b>\n"
        f"<b>✅ completed:</b> <b>{completed}</b>\n"
        f"<b>⚠ disputed:</b> <b>{disputed}</b>",
        reply_markup=admin_panel_kb(),
    )
    await cb.answer()


@router.callback_query(F.data == "admin:find")
async def admin_find_prompt(cb: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_deal_lookup)
    await send_banner(
        cb.message,
        settings,
        "<b>🔎 Введите ID сделки или token (start_token).</b>",
    )
    await cb.answer()


@router.message(AdminStates.waiting_deal_lookup)
async def admin_find_handle(message: Message, state: FSMContext, settings: Settings, storage: Storage) -> None:
    if not _is_admin(message.from_user.id, settings):
        await state.clear()
        return

    query = (message.text or "").strip()
    deal = None
    if query.isdigit():
        deal = await storage.get_deal_by_id(int(query))
    if not deal:
        deal = await storage.get_deal_by_token(query)

    await state.clear()
    if not deal:
        await send_banner(
            message,
            settings,
            "<b>❌ Сделка не найдена.</b>",
            reply_markup=admin_panel_kb(),
        )
        return

    await send_banner(
        message,
        settings,
        _deal_card(deal),
        reply_markup=admin_deal_actions_kb(deal.id),
    )


@router.callback_query(F.data.startswith("admin:deals:"))
async def admin_deals(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return
    offset = int(cb.data.split(":")[2])
    deals = await storage.list_deals(limit=5, offset=offset)
    if not deals:
        await send_banner(cb.message, settings, "<b>🧾 Список сделок пуст.</b>", reply_markup=admin_panel_kb())
        await cb.answer()
        return

    body = "\n".join(_deal_line(deal) for deal in deals)
    has_next = len(await storage.list_deals(limit=1, offset=offset + 5)) > 0
    await send_banner(
        cb.message,
        settings,
        f"<b>🧾 Последние сделки (offset {offset})</b>\n\n{body}\n\n<b>Чтобы открыть карточку, нажмите: /deal_ID</b>",
        reply_markup=admin_deals_page_kb(offset=offset, has_next=has_next, mode="deals"),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin:filter:"))
async def admin_filter_deals(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return
    _, _, status, offset_raw = cb.data.split(":")
    offset = int(offset_raw)
    deals = await storage.list_deals(limit=5, offset=offset, status=status)
    if not deals:
        await send_banner(
            cb.message,
            settings,
            f"<b>Нет сделок со статусом {status}.</b>",
            reply_markup=admin_panel_kb(),
        )
        await cb.answer()
        return

    body = "\n".join(_deal_line(deal) for deal in deals)
    has_next = len(await storage.list_deals(limit=1, offset=offset + 5, status=status)) > 0
    await send_banner(
        cb.message,
        settings,
        f"<b>🧾 Сделки со статусом {status} (offset {offset})</b>\n\n{body}\n\n<b>Чтобы открыть карточку, нажмите: /deal_ID</b>",
        reply_markup=admin_deals_page_kb(offset=offset, has_next=has_next, mode="filter", value=status),
    )
    await cb.answer()


@router.message(F.text.regexp(r"^/deal_(\d+)$"))
async def admin_open_deal_card(message: Message, settings: Settings, storage: Storage) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    deal_id = int((message.text or "").split("_", 1)[1])
    deal = await storage.get_deal_by_id(deal_id)
    if not deal:
        await send_banner(message, settings, "<b>❌ Сделка не найдена.</b>", reply_markup=admin_panel_kb())
        return
    await send_banner(message, settings, _deal_card(deal), reply_markup=admin_deal_actions_kb(deal.id))


@router.callback_query(F.data.startswith("admin:deal:"))
async def admin_refresh_deal(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return
    deal_id = int(cb.data.split(":")[2])
    deal = await storage.get_deal_by_id(deal_id)
    if not deal:
        await send_banner(cb.message, settings, "<b>❌ Сделка не найдена.</b>", reply_markup=admin_panel_kb())
        await cb.answer()
        return
    await send_banner(cb.message, settings, _deal_card(deal), reply_markup=admin_deal_actions_kb(deal.id))
    await cb.answer()


@router.callback_query(F.data.startswith("admin:set:"))
async def admin_set_status(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return
    _, _, deal_id_raw, status = cb.data.split(":")
    deal_id = int(deal_id_raw)
    changed = await storage.update_deal_status(deal_id, status)
    if not changed:
        await send_banner(cb.message, settings, "<b>❌ Сделка не найдена.</b>", reply_markup=admin_panel_kb())
        await cb.answer()
        return
    deal = await storage.get_deal_by_id(deal_id)
    await send_banner(
        cb.message,
        settings,
        f"<b>✅ Статус сделки #{deal_id} изменен на {status}.</b>\n\n{_deal_card(deal) if deal else ''}",
        reply_markup=admin_deal_actions_kb(deal_id),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin:delete:"))
async def admin_delete_deal(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    if not _is_admin(cb.from_user.id, settings):
        await cb.answer("Нет доступа", show_alert=True)
        return
    deal_id = int(cb.data.split(":")[2])
    ok = await storage.delete_deal(deal_id)
    text = f"<b>🗑 Сделка #{deal_id} удалена.</b>" if ok else "<b>❌ Сделка не найдена.</b>"
    await send_banner(cb.message, settings, text, reply_markup=admin_panel_kb())
    await cb.answer()


@router.message(F.text == "/admin")
async def admin_cmd(message: Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    await send_banner(
        message,
        settings,
        "<b>🛡 Админ-панель</b>\n\n<b>Выберите действие:</b>",
        reply_markup=admin_panel_kb(),
    )


@router.message(F.text == "/whoami")
async def whoami(message: Message, settings: Settings, storage: Storage) -> None:
    await send_banner(
        message,
        settings,
        f"<b>Ваш user_id: {message.from_user.id}</b>\n<b>Owner_id: {settings.owner_id}</b>",
        reply_markup=main_menu_kb(is_admin=message.from_user.id == settings.owner_id),
    )
