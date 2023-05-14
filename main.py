import json
import sqlite3
import re
import asyncio
import KeyBoards as kb
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime
from tonsdk.utils import Address
from pytonconnect import TonConnect
from pytonconnect.exceptions import UserRejectsError
from config import api_token, owner_id

class States(StatesGroup):
    AddAdmin = State()
    RemoveAdmin = State()


con = sqlite3.connect("DB.db", check_same_thread=False)
cur = con.cursor()

bot = Bot(token=api_token)
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT id_tg FROM Users WHERE id_tg == {message.from_user.id}").fetchall():
        cur.execute(f"INSERT INTO Users (id_tg, username) VALUES ({message.from_user.id}, '{message.from_user.username}')")
        con.commit()
    id = cur.execute(f"SELECT id FROM Users WHERE id_tg == {message.from_user.id}").fetchall()[0][0]
    if str(message.from_user.id) == owner_id:
        await message.answer("Hi, I'm a bot that will help you set up access to chats using SBT", reply_markup=kb.OwnerKb)
    elif cur.execute(f"SELECT id FROM Admins WHERE id_users == {id}").fetchall():
        await message.answer("Hi, I'm a bot that will help you set up access to chats using SBT", reply_markup=kb.AdminKb)
    else:
        await message.answer("Hi, I'm a bot that will help you set up access to chats using SBT", reply_markup=kb.UserKb)
    await state.finish()

@dp.message_handler(text="Check my SBT", state='*')
async def check_sbt(message: types.Message, state: FSMContext):
    address = cur.execute(f"SELECT address FROM Users WHERE id_tg == {message.from_user.id}").fetchall()[0][0]
    if address == None:
        connector = TonConnect(manifest_url='https://raw.githubusercontent.com/XaBbl4/pytonconnect/main/pytonconnect-manifest.json')
        is_connected = await connector.restore_connection()
        
        wallets_list = connector.get_wallets()

        generated_url_tonkeep = await connector.connect(wallets_list[0])
        generated_url_tonhub = "ok"
        msg = await message.answer(f"To verify your SBT, you need to connect your wallet.\nTonkeeper Link:{generated_url_tonkeep}\nTonhub Link:{generated_url_tonhub}")

        flag = True
        while f:
            await asyncio.sleep(1)
            if connector.connected:
                if connector.account.address:
                    flag = False
                    address = Address(connector.account.address).to_string(True, True, True)
                break
        
        await msg.delete()
        cur.execute(f"UPDATE Users SET address = '{address}' WHERE id_tg = {message.from_user.id}")
        con.commit()

@dp.message_handler(text="Add new SBT", state='*')
async def add_sbt(message: types.Message, state: FSMContext):
    pass

@dp.message_handler(text="Add new admin", state='*')
async def add_admin(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == owner_id:
        await bot.send_message(message.from_user.id, 'To add a new admin, send his username.\n(In order for a user to become an admin, he must launch this bot at least once)\nExample: "@username"')
        await States.AddAdmin.set()
    else: 
        await message.answer("You don't have enough permission")

@dp.message_handler(text="Remove admin", state='*')
async def remove_admin(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == owner_id:
        await bot.send_message(message.from_user.id, 'To remove admin, send his username.\nExample: "@username"')
        await States.RemoveAdmin.set()
    else: 
        await message.answer("You don't have enough permission")

@dp.message_handler(state = States.AddAdmin)
async def check_to_add_admin(message: types.Message, state: FSMContext):
    if ('@' not in message.text):
        await message.answer("incorrectly entered a username")
        return
    username = re.search(r'@(\w+)', message.text).string[1::]
    id = cur.execute(f"SELECT id FROM Users WHERE username == '{username}'").fetchall()
    id_tg = cur.execute(f"SELECT id_tg FROM Users WHERE username == '{username}'").fetchall()[0][0]
    if str(id_tg) == owner_id:
        await message.answer("This user is the owner")
    elif id:
        if not cur.execute(f"SELECT id FROM Admins WHERE id_users == {id[0][0]}").fetchall():
            cur.execute(f"INSERT INTO Admins (id_users) VALUES ({id[0][0]})")
            con.commit()
            await message.answer("The user is assigned as an admin")
            await bot.send_message(id_tg, "You have been appointed as an admin", reply_markup=kb.AdminKb)
            await state.finish()
        else: 
            await message.answer("This user is already an admin")
    else:
        await message.answer("This user has never started a bot or incorrectly entered a username")

@dp.message_handler(state = States.RemoveAdmin)
async def check_to_add_admin(message: types.Message, state: FSMContext):
    if ('@' not in message.text):
        await message.answer("incorrectly entered a username")
        return
    username = re.search(r'@(\w+)', message.text).string[1::]
    id = cur.execute(f"SELECT id FROM Users WHERE username == '{username}'").fetchall()
    id_tg = cur.execute(f"SELECT id_tg FROM Users WHERE username == '{username}'").fetchall()[0][0]
    if str(id_tg) == owner_id:
        await message.answer("This user is the owner")
    elif id:
        if cur.execute(f"SELECT id FROM Admins WHERE id_users == {id[0][0]}").fetchall():
            cur.execute(f"DELETE from Admins where id_users == {id[0][0]}")
            con.commit()
            await message.answer("The user has been removed from the admin position")
            await bot.send_message(id_tg, "You have been removed from the admin position", reply_markup=kb.UserKb)
            await state.finish()
        else: 
            await message.answer("This user is not an admin")
    else:
        await message.answer("This user has never started a bot or incorrectly entered a username")

@dp.message_handler(state = '*')
async def unknown_command(message: types.Message):
    await message.answer("unknown command")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)