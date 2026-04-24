from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.i18n import LANGUAGES, tr


def main_menu_kb(lang: str = "ru", is_admin: bool = False, is_worker: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{tr(lang, 'menu_create')}", callback_data="menu:create_deal")],
        [
            InlineKeyboardButton(text=f"{tr(lang, 'menu_profile')}", callback_data="menu:profile"),
            InlineKeyboardButton(text=f"{tr(lang, 'menu_requisites')}", callback_data="menu:requisites")
        ],
        [
            InlineKeyboardButton(text="📋 Мои сделки", callback_data="menu:my_deals:0")
        ],
        [
            InlineKeyboardButton(text=f"{tr(lang, 'menu_ref')}", callback_data="menu:ref"),
            InlineKeyboardButton(text=f"{tr(lang, 'menu_guarantees')}", callback_data="menu:guarantees")
        ],
    ]
    
    if is_worker:
        rows.append([InlineKeyboardButton(text="📖 Инструкция для воркеров", callback_data="menu:worker_guide")])
    
    rows.append([
        InlineKeyboardButton(text=f"{tr(lang, 'menu_lang')}", callback_data="menu:lang"),
        InlineKeyboardButton(text=f"{tr(lang, 'menu_support')}", url="https://t.me/EIfOtcSupport")
    ])
    
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛡 Админ-панель", callback_data="admin:panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def buyer_deal_kb(deal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"deal:paid:{deal_id}")],
            [InlineKeyboardButton(text="🔙 В меню", callback_data="menu:main")],
        ]
    )


def seller_deal_kb(deal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В меню", callback_data="menu:main")],
        ]
    )


def requisites_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌔 Добавить/изменить TON-кошелек", callback_data="req:ton")],
            [InlineKeyboardButton(text="💳 Добавить/изменить карту", callback_data="req:card")],
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="menu:main")],
        ]
    )


def back_menu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=tr(lang, "back_menu"), callback_data="menu:main")]]
    )


def payout_method_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 На TON-кошелек", callback_data="deal:payout_ton")],
            [InlineKeyboardButton(text="💳 На карту", callback_data="deal:payout_card")],
            [InlineKeyboardButton(text="⭐ Звезды", callback_data="deal:payout_stars")],
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="menu:main")],
        ]
    )


def missing_method_kb(method: str) -> InlineKeyboardMarkup:
    if method == "ton":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить кошелек", callback_data="req:ton")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="menu:main")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить карту", callback_data="req:card")],
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="menu:main")],
        ]
    )


def amount_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💱 Изменить валюту", callback_data="deal:currency")],
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="menu:main")],
        ]
    )


def currency_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 RUB", callback_data="cur:RUB"),
                InlineKeyboardButton(text="🇺🇦 UAH", callback_data="cur:UAH"),
                InlineKeyboardButton(text="🇰🇿 KZT", callback_data="cur:KZT"),
                InlineKeyboardButton(text="🇧🇾 BYN", callback_data="cur:BYN"),
            ],
            [
                InlineKeyboardButton(text="🇺🇿 UZS", callback_data="cur:UZS"),
                InlineKeyboardButton(text="🌔 USDT", callback_data="cur:USDT"),
                InlineKeyboardButton(text="🇪🇺 EUR", callback_data="cur:EUR"),
                InlineKeyboardButton(text="💎 TON", callback_data="cur:TON"),
            ],
            [InlineKeyboardButton(text="🔙 Назад к сумме", callback_data="deal:amount_back")],
        ]
    )


def language_kb() -> InlineKeyboardMarkup:
    rows = []
    for code, label in LANGUAGES.items():
        rows.append([InlineKeyboardButton(text=f"{code.upper()} - {label}", callback_data=f"lang:{code}")])
    rows.append([InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Общая статистика", callback_data="admin:stats")],
            [
                InlineKeyboardButton(text="📢 Рассылка (ALL)", callback_data="admin:broadcast"),
                InlineKeyboardButton(text="💬 Рассылка (TOPIC)", callback_data="admin:broadcast_topic"),
            ],
            [InlineKeyboardButton(text="🧾 Последние сделки", callback_data="admin:deals:0")],
            [InlineKeyboardButton(text="🔎 Найти сделку (ID/токен)", callback_data="admin:find")],
            [InlineKeyboardButton(text="✅ Сделки: completed", callback_data="admin:filter:completed:0")],
            [InlineKeyboardButton(text="🕒 Сделки: created", callback_data="admin:filter:created:0")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="menu:main")],
        ]
    )


def admin_deals_page_kb(offset: int, has_next: bool, mode: str = "all", value: str = "all") -> InlineKeyboardMarkup:
    prev_offset = max(0, offset - 5)
    next_offset = offset + 5
    prev_cb = f"admin:{mode}:{value}:{prev_offset}" if mode != "deals" else f"admin:deals:{prev_offset}"
    next_cb = f"admin:{mode}:{value}:{next_offset}" if mode != "deals" else f"admin:deals:{next_offset}"
    rows = []
    nav = [InlineKeyboardButton(text="⬅ Назад", callback_data=prev_cb)]
    if has_next:
        nav.append(InlineKeyboardButton(text="Вперед ➡", callback_data=next_cb))
    rows.append(nav)
    rows.append([InlineKeyboardButton(text="🛡 В админ-панель", callback_data="admin:panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_deal_actions_kb(deal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data=f"admin:deal:{deal_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin:delete:{deal_id}"),
            ],
            [
                InlineKeyboardButton(text="💸 paid", callback_data=f"admin:set:{deal_id}:paid"),
                InlineKeyboardButton(text="✅ completed", callback_data=f"admin:set:{deal_id}:completed"),
            ],
            [
                InlineKeyboardButton(text="⚠ disputed", callback_data=f"admin:set:{deal_id}:disputed"),
                InlineKeyboardButton(text="❌ cancelled", callback_data=f"admin:set:{deal_id}:cancelled"),
            ],
            [InlineKeyboardButton(text="🛡 В админ-панель", callback_data="admin:panel")],
        ]
    )


def my_deals_kb(offset: int, has_next: bool) -> InlineKeyboardMarkup:
    prev_offset = max(0, offset - 5)
    next_offset = offset + 5
    rows = []
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"menu:my_deals:{prev_offset}"))
    if has_next:
        nav.append(InlineKeyboardButton(text="Вперед ➡", callback_data=f"menu:my_deals:{next_offset}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_deal_card_kb(deal_id: int, user_role: str) -> InlineKeyboardMarkup:
    """user_role: 'seller' or 'buyer'"""
    rows = []
    if user_role == "buyer":
        rows.append([InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"deal:paid:{deal_id}")])
    rows.append([InlineKeyboardButton(text="🔙 К моим сделкам", callback_data="menu:my_deals:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
