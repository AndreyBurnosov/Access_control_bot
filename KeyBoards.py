from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


check_sbt = KeyboardButton('Check my SBT')
add_new_sbt = KeyboardButton('Add new SBT')
add_new_admin = KeyboardButton('Add new admin')
remove_admin = KeyboardButton('Remove admin')

AdminKb = ReplyKeyboardMarkup(resize_keyboard=True).add(check_sbt).add(add_new_sbt)

OwnerKb = ReplyKeyboardMarkup(resize_keyboard=True).add(check_sbt).add(add_new_sbt).add(add_new_admin).add(remove_admin)

UserKb = ReplyKeyboardMarkup(resize_keyboard=True).add(check_sbt)
