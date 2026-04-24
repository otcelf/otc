from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardMarkup

from bot.config import Settings


def support_link_kb(text: str, support_username: str) -> InlineKeyboardMarkup:
    clean_username = support_username.lstrip("@")
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, url=f"https://t.me/{clean_username}")]]
    )


async def send_banner(
    message: Message,
    settings: Settings,
    text: str,
    reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup | None = None,
) -> None:
    # If it's a callback, try to edit the caption first
    if hasattr(message, "edit_caption"):
        try:
            await message.edit_caption(caption=text, reply_markup=reply_markup)
            return
        except Exception:
            pass

    banner = Path(settings.banner_path)
    if banner.exists():
        await message.answer_photo(photo=FSInputFile(banner), caption=text, reply_markup=reply_markup)
        return
    await message.answer(text, reply_markup=reply_markup)


async def send_banner_to_chat(
    bot: Bot,
    settings: Settings,
    chat_id: int,
    text: str,
    reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup | None = None,
    message_thread_id: int | None = None,
) -> None:
    banner = Path(settings.banner_path)
    if banner.exists():
        await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(banner),
            caption=text,
            reply_markup=reply_markup,
            message_thread_id=message_thread_id,
        )
        return
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        message_thread_id=message_thread_id,
    )
