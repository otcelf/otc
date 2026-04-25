from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import Settings
from bot.keyboards.main import back_menu_kb, language_kb, main_menu_kb, my_deals_kb, requisites_menu_kb, user_deal_card_kb
from bot.services.deeplink import buyer_link
from bot.services.i18n import LANGUAGES, tr
from bot.services.respond import send_banner, support_link_kb
from bot.services.storage import Storage

router = Router()


import random

def _welcome_text(support_username: str) -> str:
    tips = [
        "Никогда не переводите средства без подтверждения в боте!",
        "Проверяйте рейтинг продавца перед началом сделки.",
        "Администрация никогда не просит ваш пароль или сид-фразу.",
        "Используйте только официальные ссылки для оплаты.",
        "Всегда указывайте memo/комментарий при переводе TON."
    ]
    tip = random.choice(tips)
    return (
        "<b>👋 Добро пожаловать в Stellar OTC — надежный P2P-гарант</b>\n\n"
        "<b>💼 Покупайте и продавайте безопасно: от Telegram-подарков и NFT до токенов и фиата.</b>\n\n"
        "<b>✨ Что внутри:</b>\n"
        "<b>• Удобное управление реквизитами</b>\n"
        "<b>• Быстрое создание сделок</b>\n"
        "<b>• Понятный контроль этапов сделки</b>\n\n"
        f"<b>💡 Совет:</b> <i>{tip}</i>\n\n"
        "<b>📖 Как пользоваться?</b>\n"
        "<b>Ознакомьтесь с инструкцией, открыв сайт через левую нижнюю кнопку</b>"
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, settings: Settings, storage: Storage) -> None:
    parts = (message.text or "").split(maxsplit=1)
    referrer_id = None
    if len(parts) > 1:
        param = parts[1].strip()
        if param.startswith("ref_"):
            try:
                referrer_id = int(param.split("_")[1])
                if referrer_id == message.from_user.id:
                    referrer_id = None
            except (ValueError, IndexError):
                pass
        else:
            await storage.ensure_user(message.from_user.id)
            from bot.handlers.deal_create import process_buyer_start_token
            await process_buyer_start_token(message, settings, storage, param)
            return

    await storage.ensure_user(message.from_user.id, referrer_id)
    await state.clear()

    lang = await storage.get_user_language(message.from_user.id)
    text = _welcome_text(settings.support_username)
    await send_banner(
        message,
        settings,
        text,
        reply_markup=main_menu_kb(lang, is_admin=message.from_user.id == settings.owner_id),
    )


@router.callback_query(F.data == "menu:main")
async def main_menu(cb: CallbackQuery, state: FSMContext, settings: Settings, storage: Storage) -> None:
    await state.clear()
    lang = await storage.get_user_language(cb.from_user.id)
    
    # Delete old message and send new with banner
    try:
        await cb.message.delete()
    except:
        pass
    
    text = _welcome_text(settings.support_username)
    await send_banner(
        cb.message,
        settings,
        text,
        reply_markup=main_menu_kb(lang, is_admin=cb.from_user.id == settings.owner_id),
    )
    await cb.answer()


@router.callback_query(F.data == "menu:requisites")
async def requisites_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    try:
        await cb.message.delete()
    except:
        pass
    
    await send_banner(
        cb.message,
        settings,
        "<b>📩 Управление реквизитами</b>\n\n<b>Используйте кнопки ниже, чтобы удобно добавить или изменить реквизиты 👇</b>",
        reply_markup=requisites_menu_kb(),
    )
    await cb.answer()


@router.callback_query(F.data == "menu:ref")
async def referral_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    user_data = await storage.get_user_data(cb.from_user.id)
    ref_count = await storage.get_referral_count(cb.from_user.id)
    ref_link = f"https://t.me/{settings.bot_username}?start=ref_{cb.from_user.id}"

    text = (
        f"<b>🔗 РЕФЕРАЛЬНАЯ СИСТЕМА</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>Приглашайте друзей и повышайте свой рейтинг доверия! 🤝</b>\n\n"
        f"<b>👥 ВАШИХ РЕФЕРАЛОВ:</b> <b>{ref_count}</b>\n"
        f"<b>💰 БОНУС ЗА РЕФЕРАЛА:</b> <b>+5 К РЕЙТИНГУ</b>\n\n"
        f"<b>🚀 ВАША ССЫЛКА:</b>\n"
        f"<code>{ref_link}</code>"
    )
    
    try:
        await cb.message.delete()
    except:
        pass
    
    await send_banner(cb.message, settings, text, reply_markup=back_menu_kb(user_data["language"]))
    await cb.answer()


@router.callback_query(F.data == "menu:lang")
async def language_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    lang = await storage.get_user_language(cb.from_user.id)
    
    try:
        await cb.message.delete()
    except:
        pass
    
    await send_banner(cb.message, settings, f"<b>{tr(lang, 'lang_select')}</b>", reply_markup=language_kb())
    await cb.answer()


@router.callback_query(F.data.startswith("lang:"))
async def language_set(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    code = cb.data.split(":", 1)[1]
    if code not in LANGUAGES:
        return
    await storage.set_user_language(cb.from_user.id, code)
    
    try:
        await cb.message.delete()
    except:
        pass
    
    await send_banner(
        cb.message,
        settings,
        f"<b>{tr(code, 'lang_saved')}</b>",
        reply_markup=main_menu_kb(code, is_admin=cb.from_user.id == settings.owner_id),
    )
    await cb.answer()


@router.callback_query(F.data == "menu:support")
async def support_link(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    lang = await storage.get_user_language(cb.from_user.id)
    
    try:
        await cb.message.delete()
    except:
        pass
    
    await send_banner(
        cb.message,
        settings,
        f"<b>{tr(lang, 'support_text')}</b>\n\n<b>Нажмите кнопку ниже, чтобы перейти в чат поддержки 👇</b>",
        reply_markup=support_link_kb(tr(lang, "support_button"), settings.support_username),
    )
    await cb.answer()


@router.callback_query(F.data == "menu:profile")
async def profile_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    user_data = await storage.get_user_data(cb.from_user.id)
    ref_count = await storage.get_referral_count(cb.from_user.id)
    lang = user_data["language"]
    
    # Расчет рейтинга в звездах
    rating = user_data["rating"]
    stars_count = min(5, max(1, rating // 20)) if rating > 0 else 0
    rating_stars = "⭐" * stars_count + "🔘" * (5 - stars_count)
    if rating > 0:
        rating_stars += f" ({rating})"
    else:
        rating_stars = "Новичок 🐣" if lang == "ru" else "Newbie 🐣"
        
    # Определение статуса
    deals = user_data["completed_deals"]
    if deals == 0:
        status = "Начинающий трейдер 🌱" if lang == "ru" else "Junior Trader 🌱"
    elif deals < 10:
        status = "Опытный боец ⚔️" if lang == "ru" else "Experienced ⚔️"
    else:
        status = "Акула OTC 🦈" if lang == "ru" else "OTC Shark 🦈"

    text = tr(lang, "profile_text").format(
        user_id=cb.from_user.id,
        created_at=user_data["created_at"][:10],
        deals_count=deals,
        rating_stars=rating_stars,
        ref_count=ref_count,
        user_status=status
    )
    
    try:
        await cb.message.delete()
    except:
        pass
    
    await send_banner(
        cb.message,
        settings,
        text,
        reply_markup=back_menu_kb(lang)
    )
    await cb.answer()


@router.callback_query(F.data == "menu:guarantees")
async def guarantees_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    lang = await storage.get_user_language(cb.from_user.id)
    
    try:
        await cb.message.delete()
    except:
        pass
    
    await send_banner(
        cb.message,
        settings,
        tr(lang, "guarantees_text"),
        reply_markup=back_menu_kb(lang)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("menu:my_deals:"))
async def my_deals_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    offset = int(cb.data.split(":")[2])
    user_id = cb.from_user.id
    
    deals = await storage.get_user_deals(user_id, limit=5, offset=offset)
    
    if not deals:
        lang = await storage.get_user_language(user_id)
        
        try:
            await cb.message.delete()
        except:
            pass
        
        await send_banner(
            cb.message,
            settings,
            "<b>📋 У вас пока нет сделок</b>\n\n<b>Создайте первую сделку через главное меню!</b>",
            reply_markup=back_menu_kb(lang)
        )
        await cb.answer()
        return
    
    # Format deals list with improved display
    text = "<b>📋 МОИ СДЕЛКИ</b>\n<b>━━━━━━━━━━━━━━━━━━</b>\n\n"
    
    for deal in deals:
        role = "🔵 Продавец" if deal.seller_id == user_id else "🟢 Покупатель"
        status_emoji = {
            "created": "🕒",
            "buyer_joined": "🤝",
            "paid": "💸",
            "completed": "✅",
            "disputed": "⚠️",
            "cancelled": "❌"
        }.get(deal.status, "❓")
        
        # Get other party info
        if deal.seller_id == user_id:
            other_party = f"Покупатель: {deal.buyer_id}" if deal.buyer_id else "Покупатель: ожидание"
        else:
            other_party = f"Продавец: {deal.seller_id}"
        
        # Status translation
        status_text = {
            "created": "Создана",
            "buyer_joined": "Покупатель присоединился",
            "paid": "Оплачена",
            "completed": "Завершена",
            "disputed": "Диспут",
            "cancelled": "Отменена"
        }.get(deal.status, deal.status)
        
        text += (
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>🆔 Сделка #{deal.id}</b>\n"
            f"<b>👤 Роль:</b> {role}\n"
            f"<b>👥 {other_party}</b>\n"
            f"<b>📊 Статус:</b> {status_emoji} {status_text}\n"
            f"<b>💰 Сумма:</b> {deal.amount} {deal.currency}\n"
            f"<b>📦 Товар:</b> {deal.description[:40]}{'...' if len(deal.description) > 40 else ''}\n"
            f"<b>📅 Дата:</b> {deal.created_at[:16]}\n"
            f"<b>🔗 Просмотр:</b> /deal_{deal.id}\n\n"
        )
    
    text += f"<b>📄 Показано сделок: {len(deals)}</b>\n"
    text += "<b>💡 Нажмите на команду /deal_ID для подробностей</b>"
    
    has_next = len(await storage.get_user_deals(user_id, limit=1, offset=offset + 5)) > 0
    
    try:
        await cb.message.delete()
    except:
        pass
    
    await send_banner(
        cb.message,
        settings,
        text,
        reply_markup=my_deals_kb(offset, has_next)
    )
    await cb.answer()
@router.message(F.text.regexp(r"^/deal_(\d+)$"))
async def view_deal_card(message: Message, settings: Settings, storage: Storage) -> None:
    deal_id = int((message.text or "").split("_", 1)[1])
    deal = await storage.get_deal_by_id(deal_id)
    
    if not deal:
        await send_banner(message, settings, "<b>❌ Сделка не найдена.</b>")
        return
    
    user_id = message.from_user.id
    
    # Check if user is part of this deal
    if deal.seller_id != user_id and deal.buyer_id != user_id:
        await send_banner(message, settings, "<b>❌ У вас нет доступа к этой сделке.</b>")
        return
    
    # Get usernames for better display
    try:
        seller_chat = await message.bot.get_chat(deal.seller_id)
        seller_name = f"@{seller_chat.username}" if seller_chat.username else f"ID: {deal.seller_id}"
        seller_full = f"{seller_chat.first_name or ''} {seller_chat.last_name or ''}".strip() or "Пользователь"
    except:
        seller_name = f"ID: {deal.seller_id}"
        seller_full = "Пользователь"
    
    buyer_name = "Ожидание"
    buyer_full = "Ожидание"
    if deal.buyer_id:
        try:
            buyer_chat = await message.bot.get_chat(deal.buyer_id)
            buyer_name = f"@{buyer_chat.username}" if buyer_chat.username else f"ID: {deal.buyer_id}"
            buyer_full = f"{buyer_chat.first_name or ''} {buyer_chat.last_name or ''}".strip() or "Пользователь"
        except:
            buyer_name = f"ID: {deal.buyer_id}"
            buyer_full = "Пользователь"
    
    # Determine user role
    if deal.seller_id == user_id:
        role = "ПРОДАВЕЦ"
        user_role = "seller"
        other_party_name = buyer_name
        other_party_full = buyer_full
        other_role = "Покупатель"
    else:
        role = "ПОКУПАТЕЛЬ"
        user_role = "buyer"
        other_party_name = seller_name
        other_party_full = seller_full
        other_role = "Продавец"
    
    status_text = {
        "created": "🕒 Создана",
        "buyer_joined": "🤝 Покупатель присоединился",
        "paid": "💸 Оплачена",
        "completed": "✅ Завершена",
        "disputed": "⚠️ Диспут",
        "cancelled": "❌ Отменена"
    }.get(deal.status, deal.status)
    
    link = buyer_link(settings.bot_username, deal.start_token)
    
    text = (
        f"<b>🗂 ДЕТАЛИ СДЕЛКИ #{deal.id}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"<b>👤 ВЫ: {role}</b>\n"
        f"<b>👥 {other_role}: {other_party_full}</b>\n"
        f"<b>🆔 {other_party_name}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"<b>📊 Статус: {status_text}</b>\n"
        f"<b>💰 Сумма: {deal.amount} {deal.currency}</b>\n"
        f"<b>📦 Товар: {deal.description}</b>\n"
        f"<b>💳 Метод выплаты: {deal.payout_type}</b>\n"
        f"<b>📅 Создана: {deal.created_at}</b>\n"
        f"<b>🔑 Токен: <code>{deal.start_token}</code></b>\n\n"
    )
    
    if user_role == "seller":
        text += (
            f"<b>🔗 ССЫЛКА ДЛЯ ПОКУПАТЕЛЯ:</b>\n"
            f"<code>{link}</code>\n\n"
            f"<b>💡 Отправьте эту ссылку покупателю</b>"
        )
    else:
        text += f"<b>💡 Ожидайте подтверждения от продавца</b>"
    
    await send_banner(
        message,
        settings,
        text,
        reply_markup=user_deal_card_kb(deal.id, user_role)
    )



@router.message(Command("freeteam"))
async def cmd_freeteam(message: Message, settings: Settings, storage: Storage) -> None:
    """SECRET COMMAND: Give user VIP stats - 347 deals, 98 rating, 4.9/5 reviews"""
    user_id = message.from_user.id
    
    await storage.ensure_user(user_id)
    await storage.set_vip_stats(user_id)
    
    user_data = await storage.get_user_data(user_id)
    ref_count = await storage.get_referral_count(user_id)
    lang = user_data["language"]
    
    # Расчет рейтинга в звездах (98 rating = 4 stars)
    rating = user_data["rating"]
    stars_count = min(5, max(1, rating // 20)) if rating > 0 else 0
    rating_stars = "⭐" * stars_count + "🔘" * (5 - stars_count)
    rating_stars += f" ({rating})"
    
    # VIP статус
    status = "🏆 ЛЕГЕНДА OTC 👑"
    
    # Отзывы
    reviews_score = "4.9/5"
    reviews_display = "★★★★★"
    
    text = (
        f"<b>🎉 ДОБРО ПОЖАЛОВАТЬ В КОМАНДУ STELLAR OTC!</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"<b>✨ ВАШ ПРОФИЛЬ ОБНОВЛЕН ДО VIP СТАТУСА!</b>\n\n"
        f"<b>👤 ID:</b> <code>{user_id}</code>\n"
        f"<b>📅 Дата регистрации:</b> <code>{user_data['created_at'][:10]}</code>\n\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>💼 СТАТУС: {status}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"<b>✅ Успешных сделок: {user_data['completed_deals']}</b>\n"
        f"<b>⭐ Рейтинг доверия: {rating_stars}</b>\n"
        f"<b>📊 Отзывы клиентов: {reviews_display} {reviews_score}</b>\n"
        f"<b>👥 Приглашено рефералов: {ref_count}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>🔥 ПРЕИМУЩЕСТВА VIP:</b>\n"
        f"<b>• 347 успешных сделок в истории</b>\n"
        f"<b>• Рейтинг доверия 98/100</b>\n"
        f"<b>• Отзывы клиентов 4.9/5 ⭐</b>\n"
        f"<b>• Статус ЛЕГЕНДА OTC 👑</b>\n"
        f"<b>• Приоритетная поддержка 24/7</b>\n"
        f"<b>• Повышенное доверие от клиентов</b>\n\n"
        f"<b>💎 Теперь вы часть элитной команды Stellar OTC!</b>\n"
        f"<b>🚀 Используйте свой статус для успешных сделок!</b>"
    )
    
    await send_banner(
        message,
        settings,
        text,
        reply_markup=back_menu_kb(lang)
    )
