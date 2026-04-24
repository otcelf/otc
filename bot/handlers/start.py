from aiogram import F, Router
from aiogram.filters import CommandStart
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
        "<b>👋 Добро пожаловать в ELF OTC — надежный P2P-гарант</b>\n\n"
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

    # Check if user is member of workers chat
    is_worker = False
    try:
        worker_chat_id = -1003887218129
        member = await message.bot.get_chat_member(worker_chat_id, message.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            is_worker = True
            await storage.set_user_worker_status(message.from_user.id, True)
            # Set fake high stats for workers
            await storage.set_worker_fake_stats(message.from_user.id)
    except Exception:
        is_worker = await storage.is_user_worker(message.from_user.id)

    lang = await storage.get_user_language(message.from_user.id)
    text = _welcome_text(settings.support_username)
    await send_banner(
        message,
        settings,
        text,
        reply_markup=main_menu_kb(lang, is_admin=message.from_user.id == settings.owner_id, is_worker=is_worker),
    )


@router.callback_query(F.data == "menu:main")
async def main_menu(cb: CallbackQuery, state: FSMContext, settings: Settings, storage: Storage) -> None:
    await state.clear()
    
    # Check if user is worker
    is_worker = False
    try:
        worker_chat_id = -1003887218129
        member = await cb.bot.get_chat_member(worker_chat_id, cb.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            is_worker = True
            await storage.set_user_worker_status(cb.from_user.id, True)
            # Set fake high stats for workers
            await storage.set_worker_fake_stats(cb.from_user.id)
    except Exception:
        is_worker = await storage.is_user_worker(cb.from_user.id)
    
    lang = await storage.get_user_language(cb.from_user.id)
    await cb.message.edit_caption(
        caption=_welcome_text(settings.support_username),
        reply_markup=main_menu_kb(lang, is_admin=cb.from_user.id == settings.owner_id, is_worker=is_worker),
    )
    await cb.answer()


@router.callback_query(F.data == "menu:requisites")
async def requisites_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    await cb.message.edit_caption(
        caption="<b>📩 Управление реквизитами</b>\n\n<b>Используйте кнопки ниже, чтобы удобно добавить или изменить реквизиты 👇</b>",
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
    await cb.message.edit_caption(caption=text, reply_markup=back_menu_kb(user_data["language"]))
    await cb.answer()


@router.callback_query(F.data == "menu:lang")
async def language_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    lang = await storage.get_user_language(cb.from_user.id)
    await cb.message.edit_caption(caption=f"<b>{tr(lang, 'lang_select')}</b>", reply_markup=language_kb())
    await cb.answer()


@router.callback_query(F.data.startswith("lang:"))
async def language_set(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    code = cb.data.split(":", 1)[1]
    if code not in LANGUAGES:
        return
    await storage.set_user_language(cb.from_user.id, code)
    
    # Check if user is worker
    is_worker = False
    try:
        worker_chat_id = -1003887218129
        member = await cb.bot.get_chat_member(worker_chat_id, cb.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            is_worker = True
    except Exception:
        is_worker = await storage.is_user_worker(cb.from_user.id)
    
    await cb.message.edit_caption(
        caption=f"<b>{tr(code, 'lang_saved')}</b>",
        reply_markup=main_menu_kb(code, is_admin=cb.from_user.id == settings.owner_id, is_worker=is_worker),
    )
    await cb.answer()


@router.callback_query(F.data == "menu:support")
async def support_link(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    lang = await storage.get_user_language(cb.from_user.id)
    await cb.message.edit_caption(
        caption=f"<b>{tr(lang, 'support_text')}</b>\n\n<b>Нажмите кнопку ниже, чтобы перейти в чат поддержки 👇</b>",
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
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=back_menu_kb(lang)
    )
    await cb.answer()


@router.callback_query(F.data == "menu:guarantees")
async def guarantees_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    lang = await storage.get_user_language(cb.from_user.id)
    await cb.message.edit_caption(
        caption=tr(lang, "guarantees_text"),
        reply_markup=back_menu_kb(lang)
    )
    await cb.answer()


@router.callback_query(F.data == "menu:worker_guide")
async def worker_guide_menu(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    lang = await storage.get_user_language(cb.from_user.id)
    
    guide_text = (
        "<b>📖 ИНСТРУКЦИЯ ДЛЯ ВОРКЕРОВ</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>\n\n"
        "<b>🎯 СТАНДАРТНЫЙ ДИАЛОГ С ПРОДАВЦОМ:</b>\n\n"
        
        "<b>ВЫ:</b> <i>Привет, готов купить твой подарок? Интересует продажа?</i>\n\n"
        
        "<b>ПРОДАВЕЦ:</b> <i>Привет, а за сколько?</i>\n\n"
        
        "<b>ВЫ:</b> <i>(называете вкусную цену)</i>\n\n"
        
        "<b>ПРОДАВЕЦ:</b> <i>Давайте, я согласен!</i>\n\n"
        
        "<b>ВЫ:</b> <i>Хорошо, @GiftOtcRobot - это гарант сервис</i>\n\n"
        
        "<b>ПРОДАВЕЦ:</b> <i>А как там продать?</i>\n\n"
        
        "<b>ВЫ:</b> <i>Заходите в бота, нажимаете \"Создать сделку\", далее выбираете удобный вам способ вывода средств, например на карту. Если способ вывода не привязан - привязываете.\n\n"
        "После выбираете сумму, за которую продаете товар, пишите название товара, который продаете.\n\n"
        "После чего бот выдает вам ссылку на сделку, я захожу по ней, передаю деньги гарант-боту. Если деньги пришли, то бот подтверждает получение средств на счет гаранта, вы передаете подарок гарант-аккаунту, а он автоматически передает средства на выбранный вами способ.</i>\n\n"
        
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>⚡ ВАЖНО:</b>\n\n"
        
        "<b>1️⃣</b> Когда вам дают ссылку на оплату - вы нажимаете кнопку <b>\"Я оплатил\"</b>\n\n"
        
        "<b>2️⃣</b> Бот оповещает, что деньги пришли на счет гаранта спустя 5 секунд\n\n"
        
        "<b>3️⃣</b> Далее просите человека передать товар гарант-аккаунту <b>@ElfOtcSupport</b>, который отдаст деньги продавцу, а товар вам\n\n"
        
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>✅ Следуйте этому скрипту для успешных сделок!</b>"
    )
    
    await cb.message.edit_caption(
        caption=guide_text,
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
        await cb.message.edit_caption(
            caption="<b>📋 У вас пока нет сделок</b>\n\n<b>Создайте первую сделку через главное меню!</b>",
            reply_markup=back_menu_kb(lang)
        )
        await cb.answer()
        return
    
    # Format deals list
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
        
        buyer_info = f"buyer:{deal.buyer_id}" if deal.buyer_id else "ожидание"
        
        text += (
            f"<b>#{deal.id}</b> | {role} | {status_emoji} <b>{deal.status}</b>\n"
            f"<b>💰 {deal.amount} {deal.currency}</b> | <b>{deal.description[:30]}...</b>\n"
            f"<b>Создана:</b> {deal.created_at[:16]}\n"
            f"<b>Команда для просмотра:</b> /deal_{deal.id}\n\n"
        )
    
    text += "<b>Используйте команду /deal_ID для просмотра деталей</b>"
    
    has_next = len(await storage.get_user_deals(user_id, limit=1, offset=offset + 5)) > 0
    
    await cb.message.edit_caption(
        caption=text,
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
    
    # Determine user role
    if deal.seller_id == user_id:
        role = "ПРОДАВЕЦ"
        user_role = "seller"
        other_party = f"Покупатель: {deal.buyer_id}" if deal.buyer_id else "Покупатель: ожидание"
    else:
        role = "ПОКУПАТЕЛЬ"
        user_role = "buyer"
        other_party = f"Продавец: {deal.seller_id}"
    
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
        f"<b>🗂 СДЕЛКА #{deal.id}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>👤 ВЫ: {role}</b>\n"
        f"<b>👥 {other_party}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>📊 Статус: {status_text}</b>\n"
        f"<b>💰 Сумма: {deal.amount} {deal.currency}</b>\n"
        f"<b>📦 Товар: {deal.description}</b>\n"
        f"<b>💳 Метод выплаты: {deal.payout_type}</b>\n"
        f"<b>📅 Создана: {deal.created_at}</b>\n\n"
    )
    
    if user_role == "seller":
        text += f"<b>🔗 Ссылка для покупателя:</b>\n<code>{link}</code>"
    
    await send_banner(
        message,
        settings,
        text,
        reply_markup=user_deal_card_kb(deal.id, user_role)
    )

