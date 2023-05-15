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
from config import api_token

class States(StatesGroup):
    AddAdmin = State()
    RemoveAdmin = State()


con = sqlite3.connect("DB.db", check_same_thread=False)
cur = con.cursor()

bot = Bot(token=api_token)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(state='*', content_types=['new_chat_members'])
async def update_chats(message: types.Message):
    if not cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall():
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        owner_id = -1
        for user in chat_admins:
            if user['status'] == 'creator':
                owner_id = user['user']['id']
        cur.execute(f"INSERT INTO Chats (id_tg, name, owner_id) VALUES ({message.chat.id}, '{message.chat.title}', {owner_id})")
        con.commit()
    
@dp.message_handler(commands=['start'], state='*', chat_type=types.ChatType.PRIVATE)
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


@dp.message_handler(commands=['reg'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def reg_user(message: types.Message, state: FSMContext):
    id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chats = cur.execute(f"SELECT chat_id FROM Users WHERE id_tg == {message.from_user.id}").fetchall()
    if id not in chats:
        address = cur.execute(f"SELECT address FROM Users WHERE id_tg == {message.from_user.id}").fetchall()
        if address and address[0][0] != None:
            cur.execute(f"INSERT INTO Users (id_tg, username, address, chat_id) VALUES ({message.from_user.id}, '{message.from_user.username}', '{address[0][0]}', {id})")
            con.commit()
        else:
            cur.execute(f"INSERT INTO Users (id_tg, username, chat_id) VALUES ({message.from_user.id}, '{message.from_user.username}', {id})")
            con.commit()

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
        while flag:
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

@dp.message_handler(commands=['add_admin'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def add_admin(message: types.Message, state: FSMContext):
    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    if message.from_user.id == owner_id:
        await message.answer('To add a new admin, send his username.\n(In order for a user to become an admin, he must launch this bot at least once)\nExample: "@username"\nReply for this message')
        await States.AddAdmin.set()
    else: 
        await message.answer("You don't have enough permission")
        
@dp.message_handler(commands=['remove_admin'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def remove_admin(message: types.Message, state: FSMContext):
    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    if message.from_user.id == owner_id:
        await message.answer('To remove admin, send his username.\nExample: "@username"\nReply for this message')
        await States.RemoveAdmin.set()
    else: 
        await message.answer("You don't have enough permission")

@dp.message_handler(state = States.AddAdmin, chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def check_to_add_admin(message: types.Message, state: FSMContext):
    if ('@' not in message.text):
        await message.answer("incorrectly entered a username")
        return
    username = re.search(r'@(\w+)', message.text).string[1::]

    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    id = cur.execute(f"SELECT id FROM Users WHERE username == '{username}' AND chat_id == {chat_id}").fetchall()
    id_tg = cur.execute(f"SELECT id_tg FROM Users WHERE username == '{username}'").fetchall()
    if id_tg and id_tg == owner_id:
        await message.answer("This user is the owner")
    elif id:

        admins_id = cur.execute(f"SELECT id_users FROM Admins WHERE id_users == {id[0][0]}").fetchall()
        print(admins_id)
        need_assign = -1
        for adm in admins_id:
            chat_id = cur.execute(f"SELECT chat_id FROM Users WHERE id == {adm[0]}").fetchall()[0][0]
            if message.chat.id == cur.execute(f"SELECT id_tg FROM Chats WHERE id == {chat_id}").fetchall()[0][0]:
                need_assign = adm[0]
                break

        if need_assign == -1:
            cur.execute(f"INSERT INTO Admins (id_users) VALUES ({id[0][0]})")
            con.commit()
            await message.answer("The user is assigned as an admin")
            await state.finish()
        else: 
            await message.answer("This user is already an admin")
    else:
        await message.answer("This user has never started a bot or incorrectly entered a username")

@dp.message_handler(state = States.RemoveAdmin)
async def check_to_remove_admin(message: types.Message, state: FSMContext):
    if ('@' not in message.text):
        await message.answer("incorrectly entered a username")
        return
    username = re.search(r'@(\w+)', message.text).string[1::]

    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    id = cur.execute(f"SELECT id FROM Users WHERE username == '{username}' AND chat_id == {chat_id}").fetchall()
    id_tg = cur.execute(f"SELECT id_tg FROM Users WHERE username == '{username}'").fetchall()[0][0]

    if id_tg and id_tg == owner_id:
        await message.answer("This user is the owner")
    elif id:
        
        admins_id = cur.execute(f"SELECT id_users FROM Admins WHERE id_users == {id[0][0]}").fetchall()
        print(admins_id)
        need_delete = -1
        for adm in admins_id:
            chat_id = cur.execute(f"SELECT chat_id FROM Users WHERE id == {adm[0]}").fetchall()[0][0]
            if message.chat.id == cur.execute(f"SELECT id_tg FROM Chats WHERE id == {chat_id}").fetchall()[0][0]:
                need_delete = adm[0]
                break

        if need_delete != -1:
            cur.execute(f"DELETE from Admins where id_users == {need_delete}")
            con.commit()
            await message.answer("The user has been removed from the admin position")
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