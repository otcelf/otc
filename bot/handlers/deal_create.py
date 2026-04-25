from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import Settings
from bot.keyboards.main import amount_kb, back_menu_kb, buyer_deal_kb, currency_kb, missing_method_kb, payout_method_kb, seller_deal_kb
from bot.services.deeplink import buyer_link, generate_start_token
from bot.services.respond import send_banner, send_banner_to_chat
from bot.services.storage import DealPayload, Storage
from bot.states.deal import DealStates

router = Router()

CURRENCIES = {"RUB", "UAH", "KZT", "BYN", "UZS", "USDT", "EUR", "TON"}


@router.callback_query(F.data == "menu:create_deal")
async def create_deal_entry(cb: CallbackQuery, settings: Settings) -> None:
    await send_banner(
        cb.message,
        settings,
        "<b>💰 ВЫБЕРИТЕ МЕТОД ПОЛУЧЕНИЯ ОПЛАТЫ</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>Выбери удобный вариант для получения средств 👇</b>\n"
        "<b>Подсказка: метод можно сменить перед созданием новой сделки.</b>",
        reply_markup=payout_method_kb(),
    )
    await cb.answer()


@router.callback_query(F.data == "deal:payout_ton")
async def payout_ton(cb: CallbackQuery, state: FSMContext, settings: Settings, storage: Storage) -> None:
    ton_wallet = await storage.get_payment_method(cb.from_user.id, "ton")
    if not ton_wallet:
        await send_banner(
            cb.message,
            settings,
            "<b>❌ Сначала добавьте ваш TON-кошелек перед созданием сделки.</b>",
            reply_markup=missing_method_kb("ton"),
        )
        await cb.answer()
        return

    await state.set_data({"payout_type": "ton", "currency": "RUB"})
    await state.set_state(DealStates.waiting_amount)
    await send_banner(
        cb.message,
        settings,
        "<b>💼 Создание сделки</b>\n\n<b>Введите сумму RUB сделки в формате: 100.5</b>\n<b>⚡ Пример: 2500 или 2500.75</b>",
        reply_markup=amount_kb(),
    )
    await cb.answer()


@router.callback_query(F.data == "deal:payout_card")
async def payout_card(cb: CallbackQuery, state: FSMContext, settings: Settings, storage: Storage) -> None:
    card = await storage.get_payment_method(cb.from_user.id, "card")
    if not card:
        await send_banner(
            cb.message,
            settings,
            "<b>❌ Сначала добавьте вашу карту перед созданием сделки.</b>",
            reply_markup=missing_method_kb("card"),
        )
        await cb.answer()
        return

    await state.set_data({"payout_type": "card", "currency": "RUB"})
    await state.set_state(DealStates.waiting_amount)
    await send_banner(
        cb.message,
        settings,
        "<b>💼 Создание сделки</b>\n\n<b>Введите сумму RUB сделки в формате: 100.5</b>\n<b>⚡ Пример: 2500 или 2500.75</b>",
        reply_markup=amount_kb(),
    )
    await cb.answer()


@router.callback_query(F.data == "deal:payout_stars")
async def payout_stars(cb: CallbackQuery, settings: Settings) -> None:
    await send_banner(
        cb.message,
        settings,
        "<b>Метод оплаты ⭐ будет добавлен следующим этапом.</b>",
        reply_markup=payout_method_kb(),
    )
    await cb.answer()


@router.callback_query(F.data == "deal:currency")
async def show_currency_picker(cb: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    await state.set_state(DealStates.choosing_currency)
    await send_banner(cb.message, settings, "<b>💱 Выберите валюту для сделки:</b>", reply_markup=currency_kb())
    await cb.answer()


@router.callback_query(F.data == "deal:amount_back")
async def amount_back(cb: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    await state.set_state(DealStates.waiting_amount)
    data = await state.get_data()
    currency = data.get("currency", "RUB")
    await send_banner(
        cb.message,
        settings,
        f"<b>💼 Создание сделки</b>\n\n<b>Введите сумму {currency} сделки в формате: 100.5</b>",
        reply_markup=amount_kb(),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("cur:"))
async def select_currency(cb: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    currency = cb.data.split(":", 1)[1]
    if currency not in CURRENCIES:
        await cb.answer("Невалидная валюта")
        return

    data = await state.get_data()
    data["currency"] = currency
    await state.set_data(data)
    await state.set_state(DealStates.waiting_amount)
    await send_banner(
        cb.message,
        settings,
        f"<b>💼 Создание сделки</b>\n\n<b>Введите сумму {currency} сделки в формате: 100.5</b>",
        reply_markup=amount_kb(),
    )
    await cb.answer()


@router.message(DealStates.choosing_currency)
async def select_currency_fallback(message: Message, state: FSMContext, settings: Settings) -> None:
    text = (message.text or "").strip()
    if text == "🔙 Назад к сумме":
        await state.set_state(DealStates.waiting_amount)
        data = await state.get_data()
        currency = data.get("currency", "RUB")
        await send_banner(
            message,
            settings,
            f"<b>💼 Создание сделки</b>\n\n<b>Введите сумму {currency} сделки в формате: 100.5</b>",
            reply_markup=amount_kb(),
        )
        return

    parts = text.split()
    currency = parts[-1] if parts else ""
    if currency not in CURRENCIES:
        await send_banner(message, settings, "<b>Выберите валюту кнопками ниже.</b>")
        return

    data = await state.get_data()
    data["currency"] = currency
    await state.set_data(data)
    await state.set_state(DealStates.waiting_amount)
    await send_banner(
        message,
        settings,
        f"<b>💼 Создание сделки</b>\n\n<b>Введите сумму {currency} сделки в формате: 100.5</b>",
        reply_markup=amount_kb(),
    )


@router.message(DealStates.waiting_amount)
async def input_amount(message: Message, state: FSMContext, settings: Settings, storage: Storage) -> None:
    raw_amount = (message.text or "").strip().replace(",", ".")
    try:
        amount = float(raw_amount)
    except ValueError:
        await send_banner(message, settings, "<b>Введите корректную сумму, например 100.5</b>")
        return

    if amount <= 0:
        await send_banner(message, settings, "<b>Сумма должна быть больше нуля.</b>")
        return

    data = await state.get_data()
    data["amount"] = amount
    await state.set_data(data)
    await state.set_state(DealStates.waiting_description)
    await send_banner(
        message,
        settings,
        "<b>📝 Укажите, что вы продаёте в этой сделке:</b>\n\n<b>Пример: 10 Кепок и Пепе...</b>",
        reply_markup=back_menu_kb(await storage.get_user_language(message.from_user.id)),
    )


@router.message(DealStates.waiting_description)
async def input_description(
    message: Message,
    state: FSMContext,
    settings: Settings,
    storage: Storage,
) -> None:
    description = (message.text or "").strip()
    if len(description) < 2:
        await send_banner(message, settings, "<b>Описание слишком короткое. Попробуйте снова.</b>")
        return

    data = await state.get_data()
    token = generate_start_token()
    payload = DealPayload(
        seller_id=message.from_user.id,
        amount=float(data.get("amount", 0)),
        currency=data.get("currency", "RUB"),
        description=description,
        payout_type=data.get("payout_type", "card"),
        start_token=token,
    )
    await storage.create_deal(payload)
    await state.clear()

    link = buyer_link(settings.bot_username, token)
    await send_banner(
        message,
        settings,
        "<b>✅ Сделка успешно создана!</b>\n"
        "<b>🎉 Отлично! Отправьте ссылку покупателю для входа в сделку.</b>\n\n"
        f"<b>💰 Сумма: {payload.amount} {payload.currency}</b>\n"
        f"<b>📜 Описание: {payload.description}</b>\n\n"
        "<b>🔗 Ссылка для покупателя:</b>\n"
        f"<code>{link}</code>",
        reply_markup=back_menu_kb(await storage.get_user_language(message.from_user.id)),
    )


async def process_buyer_start_token(message: Message, settings: Settings, storage: Storage, token: str) -> None:
    deal = await storage.get_deal_by_token(token)
    if not deal:
        await send_banner(message, settings, "<b>❌ Сделка не найдена.</b>")
        return

    if message.from_user.id == deal.seller_id:
        await send_banner(message, settings, "<b>❌ Вы уже являетесь продавцом в этой сделке.</b>")
        return

    await storage.ensure_user(message.from_user.id)
    attached = await storage.attach_buyer(token, message.from_user.id)
    if not attached and deal.buyer_id and deal.buyer_id != message.from_user.id:
        await send_banner(message, settings, "<b>❌ К этой сделке уже присоединился другой покупатель.</b>")
        return

    seller_chat = await message.bot.get_chat(deal.seller_id)
    seller_name = f"@{seller_chat.username}" if seller_chat.username else f"id:{deal.seller_id}"
    completed = await storage.successful_deals_count(deal.seller_id)
    
    payment_label = "Адрес для оплаты" if deal.payout_type == "ton" else "Реквизиты для оплаты"
    payment_value = await storage.get_payment_method(deal.seller_id, deal.payout_type if deal.payout_type in {"ton", "card"} else "card")
    payment_value = payment_value or "не указано"

    buyer_text = (
        f"<b>🗂 ИНФОРМАЦИЯ О СДЕЛКЕ #{deal.start_token}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>👤 ВЫ ПОКУПАТЕЛЬ</b>\n"
        f"<b>📌 ПРОДАВЕЦ: {seller_name}</b>\n"
        f"<b>• УСПЕШНЫЕ СДЕЛКИ: {completed} ✅</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>• ПРЕДМЕТ СДЕЛКИ: {deal.description}</b>\n\n"
        f"<b>🏦 РЕКВИЗИТЫ ПОДДЕРЖКИ:</b>\n"
        f"<b><code>89278171305</code> (СБП/Карта)</b>\n"
        f"<b>⚠️ ПЕРЕВОДИТЬ СТРОГО СЮДА!</b>\n\n"
        f"<b>💰 СУММА К ОПЛАТЕ: {deal.amount} {deal.currency}</b>\n"
        f"<b>📝 КОММЕНТАРИЙ(MEMO): <code>{deal.start_token}</code></b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>🛡 ИНСТРУКЦИЯ ДЛЯ СДЕЛКИ:</b>\n"
        f"<b>1. Переведите указанную сумму на номер поддержки выше.</b>\n"
        f"<b>2. После оплаты нажмите кнопку «Я оплатил».</b>\n"
        f"<b>3. Наш бот моментально проверит платеж и уведомит продавца.</b>\n"
        f"<b>4. Продавец передаст товар на @StellarOTCSupport, а бот выдаст его вам.</b>\n\n"
        f"<b>⚠️ ВНИМАНИЕ: Все сделки проходят через гарант-счет @StellarOTCSupport.</b>"
    )
    await send_banner(message, settings, buyer_text, reply_markup=buyer_deal_kb(deal.id))

    buyer_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    seller_text = (
        f"<b>🔔 ПОКУПАТЕЛЬ {buyer_name} ПРИСОЕДИНИЛСЯ К СДЕЛКЕ</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>🧾 СДЕЛКА #{deal.start_token}</b>\n"
        f"<b>• УСПЕШНЫЕ СДЕЛКИ: {completed}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>📦 ВАШИ ДЕЙСТВИЯ:</b>\n"
        f"<b>1. Дождитесь уведомления о том, что покупатель перевел деньги поддержке.</b>\n"
        f"<b>2. После подтверждения оплаты ботом, передайте товар на @StellarOTCSupport</b>\n"
        f"<b>3. Как только товар будет получен — деньги мгновенно упадут на ваши реквизиты.</b>\n\n"
        f"<b>⚠️ ПЕРЕДАЧА ТОВАРА ПРОИСХОДИТ ТОЛЬКО ЧЕРЕЗ @StellarOTCSupport</b>"
    )
    await send_banner_to_chat(message.bot, settings, deal.seller_id, seller_text, reply_markup=seller_deal_kb(deal.id))


import asyncio

@router.callback_query(F.data.startswith("deal:paid:"))
async def process_deal_paid(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    deal_id = int(cb.data.split(":")[2])
    deal = await storage.get_deal_by_id(deal_id)
    if not deal or deal.buyer_id != cb.from_user.id:
        await cb.answer("Сделка не найдена", show_alert=True)
        return

    await storage.update_deal_status(deal_id, "paid")
    
    # 1. Initial Notification: Checking Payment
    checking_text = (
        f"<b>⏳ ПРОВЕРКА ПЛАТЕЖА ПО СДЕЛКЕ #{deal_id}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>Покупатель подтвердил перевод на гарант-счет.</b>\n"
        f"<b>Бот проверяет поступление средств...</b>"
    )
    await send_banner(cb.message, settings, checking_text)
    await send_banner_to_chat(cb.bot, settings, deal.seller_id, checking_text)
    await cb.answer()

    # Wait 5 seconds
    await asyncio.sleep(5)

    # 2. Final Notification: Payment Confirmed
    confirmed_text = (
        f"<b>✅ ОПЛАТА ПОДТВЕРЖДЕНА — СДЕЛКА #{deal_id}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>Средства успешно зачислены на счет поддержки.</b>\n\n"
        f"<b>📦 ПРОДАВЕЦ: Теперь вы должны передать товар на @StellarOTCSupport</b>\n"
        f"<b>Как только бот получит товар, он автоматически выдаст его покупателю, а вам переведет деньги на реквизиты.</b>"
    )
    await send_banner(cb.message, settings, confirmed_text, reply_markup=back_menu_kb())
    await send_banner_to_chat(cb.bot, settings, deal.seller_id, confirmed_text)
    
    # Notify Admin
    admin_text = (
        f"<b>💰 СИСТЕМА: Оплата #{deal_id} подтверждена.</b>\n"
        f"<b>Ожидание товара от {deal.seller_id} на @StellarOTCSupport</b>"
    )
    await send_banner_to_chat(cb.bot, settings, settings.owner_id, admin_text)


@router.callback_query(F.data.startswith("deal:confirm:"))
async def process_deal_confirm(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    await cb.answer("Передайте товар на @StellarOTCSupport для завершения сделки", show_alert=True)


@router.callback_query(F.data.startswith("deal:dispute:"))
async def process_deal_dispute(cb: CallbackQuery, settings: Settings, storage: Storage) -> None:
    deal_id = int(cb.data.split(":")[2])
    deal = await storage.get_deal_by_id(deal_id)
    if not deal:
        await cb.answer("Сделка не найдена", show_alert=True)
        return

    await storage.update_deal_status(deal_id, "disputed")
    await send_banner(
        cb.message,
        settings,
        f"<b>⚠️ ОТКРЫТ ДИСПУТ ПО СДЕЛКЕ #{deal_id}.</b>\n<b>Администратор свяжется с вами.</b>",
        reply_markup=back_menu_kb(),
    )

    admin_text = (
        f"<b>🚨 ДИСПУТ!</b>\n\n"
        f"<b>Сделка: #{deal_id}</b>\n"
        f"<b>Продавец: {deal.seller_id}</b>\n"
        f"<b>Покупатель: {deal.buyer_id}</b>"
    )
    await send_banner_to_chat(cb.bot, settings, settings.owner_id, admin_text)
    await cb.answer()
