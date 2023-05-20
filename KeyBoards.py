from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TonkeeperButton = KeyboardButton('Tonkeeper')
TonhubButton = KeyboardButton('Tonhub')

Walletkb = ReplyKeyboardMarkup(resize_keyboard=True).add(TonkeeperButton).add(TonhubButton)
