import json
import sqlite3
import re
import asyncio
import KeyBoards as kb
import requests
import qrcode
import os
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.markdown import link
from aiogram.types.input_file import InputFile
from datetime import datetime
from tonsdk.utils import Address
from pytonconnect import TonConnect
from pytonconnect.exceptions import UserRejectsError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from support import build_bd
from config import api_token, bot_id

class States(StatesGroup):
    AddAdmin = State()
    RemoveAdmin = State()
    AddNFT = State() 
    RemoveNFT = State()


con = sqlite3.connect("DB.db", check_same_thread=False)
cur = con.cursor()

build_bd(cur, con)

bot = Bot(token=api_token)
dp = Dispatcher(bot, storage=MemoryStorage())

scheduler = AsyncIOScheduler()


@dp.chat_join_request_handler()
async def check_to_accept_user(update: types.ChatJoinRequest):
    if not cur.execute(f"SELECT id_tg FROM Users WHERE id_tg == {update.from_user.id}").fetchall():
        cur.execute(f"INSERT INTO Users (id_tg, username) VALUES ({update.from_user.id}, '{update.from_user.username}')")
        con.commit()
    if cur.execute(f"SELECT address FROM Users WHERE id_tg == {update.from_user.id}").fetchall()[0][0] is None:
        await bot.send_message(chat_id=update.from_user.id, text="To join the group, connect your wallet (Tonkeeper or Tonhub)🚀", reply_markup=kb.Walletkb)
    else:
        address = cur.execute(f"SELECT address FROM Users WHERE id_tg == {update.from_user.id}").fetchall()[0][0]
        chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {update.chat.id}").fetchall()[0][0]
        i = 0
        nfts = cur.execute(f"SELECT collection_address FROM Passes WHERE chat_id == {chat_id}").fetchall()
        while i < len(nfts):
            url = f'https://tonapi.io/v2/accounts/{address}/nfts?collection={nfts[i]}&limit=1000&offset=0&indirect_ownership=false'
            try:
                response = requests.get(url).json()
            except:
                continue
            if response:
                id = cur.execute(f"SELECT id FROM Users WHERE id_tg == {update.from_user.id}").fetchall()[0][0]
                cur.execute(f"INSERT INTO Members (user_id, chat_id) VALUES ({id}, {chat_id})")
                con.commit()
                await update.approve()
                return
            else:
                i += 1
        await bot.send_message(chat_id=update.from_user.id, text="You don't have the necessary NFT to join the group 😢")
        
        

@dp.message_handler(text = 'Tonkeeper', state='*', chat_type=types.ChatType.PRIVATE)
async def connect_wallet_tonkeeper(message: types.Message):
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json')
    is_connected = await connector.restore_connection()
    
    wallets_list = connector.get_wallets()

    generated_url_tonkeeper = await connector.connect(wallets_list[0])
    urlkb = InlineKeyboardMarkup(row_width=1)
    urlButton = InlineKeyboardButton(text='Open Tonkeeper', url=generated_url_tonkeeper)        
    urlkb.add(urlButton)
    img = qrcode.make(generated_url_tonkeeper)
    path = f'image{random.randint(0, 100000)}.png'
    img.save(path)
    photo = InputFile(path)
    msg = await bot.send_photo(chat_id=message.chat.id, photo=photo, reply_markup=urlkb)
    os.remove(path)

    flag = True
    while flag:
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                flag = False
                address = Address(connector.account.address).to_string(True, True, True)
            break
    
    await msg.delete()
    await bot.send_message(message.from_user.id, 'Your wallet has been successfully connect.👌\nSend the application again🔄')
    cur.execute(f"UPDATE Users SET address = '{address}' WHERE id_tg = {message.from_user.id}")
    con.commit()

@dp.message_handler(text = 'Tonhub', state='*', chat_type=types.ChatType.PRIVATE)
async def connect_wallet_tonhub(message: types.Message):
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json')
    is_connected = await connector.restore_connection()
    
    wallets_list = connector.get_wallets()

    generated_url_tonhub = await connector.connect(wallets_list[1])
    urlkb = InlineKeyboardMarkup(row_width=1)
    urlButton = InlineKeyboardButton(text='Open Tonhub', url=generated_url_tonhub)
    urlkb.add(urlButton)
    img = qrcode.make(generated_url_tonhub)
    path = f'image{random.randint(0, 100000)}.png'
    img.save(path)
    photo = InputFile(path)
    msg = await bot.send_photo(chat_id=message.chat.id, photo=photo, reply_markup=urlkb)
    os.remove(path)

    flag = True
    while flag:
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                flag = False
                address = Address(connector.account.address).to_string(True, True, True)
            break
    
    await msg.delete()
    await bot.send_message(message.from_user.id, 'Your wallet has been successfully connect.👌\nSend the application again 🔄')
    cur.execute(f"UPDATE Users SET address = '{address}' WHERE id_tg = {message.from_user.id}")
    con.commit()

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

@dp.message_handler(state='*', content_types=['left_chat_member'])
async def update_members(message: types.Message):
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    if message.left_chat_member.id == bot_id:
        cur.execute(f"DELETE FROM Members WHERE chat_id == {chat_id}")
        con.commit()
        cur.execute(f"DELETE FROM Admins WHERE chat_id == {chat_id}")
        con.commit()
        cur.execute(f"DELETE FROM Passes WHERE chat_id == {chat_id}")
        con.commit()
        cur.execute(f"DELETE FROM Chats WHERE id_tg == {message.chat.id}")
        con.commit()
    elif not message.left_chat_member.is_bot:
        user_id = cur.execute(f"SELECT id FROM Users WHERE id_tg == {message.left_chat_member.id}").fetchall()[0][0]
        cur.execute(f"DELETE FROM Admins WHERE id_users == {user_id} AND chat_id == {chat_id}")
        con.commit()
        cur.execute(f"DELETE FROM Members WHERE user_id == {user_id} AND chat_id == {chat_id}")
        con.commit()

@dp.message_handler(commands=['add_nft'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def add_nft(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall():
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        owner_id = -1
        for user in chat_admins:
            if user['status'] == 'creator':
                owner_id = user['user']['id']
        cur.execute(f"INSERT INTO Chats (id_tg, name, owner_id) VALUES ({message.chat.id}, '{message.chat.title}', {owner_id})")
        con.commit()

    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    admins = cur.execute(f"SELECT id_users FROM Admins WHERE chat_id == {chat_id}").fetchall()

    users = []
    for adm in admins:
        users.append(cur.execute(f"SELECT id_tg FROM Users WHERE id == {adm[0]}").fetchall()[0][0])
    users.append(owner_id) 
    
    if message.from_user.id in users:
        await message.answer('To add a new NFT for access, send colection address.\n❗️Reply for this message❗️')
        await States.AddNFT.set()
    else: 
        await message.answer("You don't have enough permission ❌")
        await message.delete()

@dp.message_handler(commands=['remove_nft'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def remove_nft(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall():
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        owner_id = -1
        for user in chat_admins:
            if user['status'] == 'creator':
                owner_id = user['user']['id']
        cur.execute(f"INSERT INTO Chats (id_tg, name, owner_id) VALUES ({message.chat.id}, '{message.chat.title}', {owner_id})")
        con.commit()

    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    admins = cur.execute(f"SELECT id_users FROM Admins WHERE chat_id == {chat_id}").fetchall()

    users = []
    for adm in admins:
        users.append(cur.execute(f"SELECT id_tg FROM Users WHERE id == {adm[0]}").fetchall()[0][0])
    users.append(owner_id) 
    
    if message.from_user.id in users:
        await message.answer('To remove NFT for access, send colection address.\n❗️Reply for this message❗️')
        await States.RemoveNFT.set()
    else: 
        await message.answer("You don't have enough permission ❌")
        await message.delete()

@dp.message_handler(commands=['show_nft'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def show_nft(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall():
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        owner_id = -1
        for user in chat_admins:
            if user['status'] == 'creator':
                owner_id = user['user']['id']
        cur.execute(f"INSERT INTO Chats (id_tg, name, owner_id) VALUES ({message.chat.id}, '{message.chat.title}', {owner_id})")
        con.commit()
    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    admins = cur.execute(f"SELECT id_users FROM Admins WHERE chat_id == {chat_id}").fetchall()

    users = []
    for adm in admins:
        users.append(cur.execute(f"SELECT id_tg FROM Users WHERE id == {adm[0]}").fetchall()[0][0])
    users.append(owner_id) 
    
    if message.from_user.id in users:
        nfts = cur.execute(f"SELECT collection_address FROM Passes WHERE chat_id == {chat_id}").fetchall()
        if not nfts:
            await message.answer(f'There are no valid passes in this group❗️')
            await state.finish()
            return
        text = ''
        for i in range(len(nfts)):
            url = f'https://tonapi.io/v2/nfts/collections/{nfts[i][0]}'
            response = requests.get(url).json()
            name = response['metadata']['name']
            link = f'https://tonscan.org/nft/{nfts[i][0]}'
            text += f'{i + 1}\) ' + '*' + '[' + name + ']' + '(' + link + ') ' + '*' + '`' + nfts[i][0] + '`' + '\n\n'
        
        await message.answer(f'List of NFTs Providing Users Access:\n\n{text}', parse_mode='MarkdownV2', disable_web_page_preview=True)
        await state.finish()
    else: 
        await message.answer("You don't have enough permission ❌")
        await message.delete()

@dp.message_handler(commands=['add_admin'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def add_admin(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall():
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        owner_id = -1
        for user in chat_admins:
            if user['status'] == 'creator':
                owner_id = user['user']['id']
        cur.execute(f"INSERT INTO Chats (id_tg, name, owner_id) VALUES ({message.chat.id}, '{message.chat.title}', {owner_id})")
        con.commit()

    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    if message.from_user.id == owner_id:
        await message.answer('To add a new admin, send his username.\n⚠️ Example: "@username"\n❗️Reply for this message❗️')
        await States.AddAdmin.set()
    else: 
        await message.answer("You don't have enough permission ❌")
        await message.delete()
        
@dp.message_handler(commands=['remove_admin'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def remove_admin(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall():
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        owner_id = -1
        for user in chat_admins:
            if user['status'] == 'creator':
                owner_id = user['user']['id']
        cur.execute(f"INSERT INTO Chats (id_tg, name, owner_id) VALUES ({message.chat.id}, '{message.chat.title}', {owner_id})")
        con.commit()

    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    if message.from_user.id == owner_id:
        await message.answer('To remove admin, send his username.\n⚠️ Example: "@username"\n❗️Reply for this message❗️')
        await States.RemoveAdmin.set()
    else: 
        await message.answer("You don't have enough permission ❌")
        await message.delete()

@dp.message_handler(commands=['reg'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def remove_admin(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall():
        chat_admins = await bot.get_chat_administrators(message.chat.id)
        owner_id = -1
        for user in chat_admins:
            if user['status'] == 'creator':
                owner_id = user['user']['id']
        cur.execute(f"INSERT INTO Chats (id_tg, name, owner_id) VALUES ({message.chat.id}, '{message.chat.title}', {owner_id})")
        con.commit()

    bot_username = await bot.get_me()
    bot_username = bot_username.username

    if not cur.execute(f"SELECT id_tg FROM Users WHERE id_tg == {message.from_user.id}").fetchall():
        cur.execute(f"INSERT INTO Users (id_tg, username) VALUES ({message.from_user.id}, '{message.from_user.username}')")
        con.commit()
        chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
        id = cur.execute(f"SELECT id FROM Users WHERE id_tg == {message.from_user.id}").fetchall()[0][0]
        cur.execute(f"INSERT INTO Members (user_id, chat_id) VALUES ({id}, {chat_id})")
        con.commit()
        await message.answer(f'@{message.from_user.username} have successfully registered ✅\n')
    if cur.execute(f"SELECT address FROM Users WHERE id_tg == {message.from_user.id}").fetchall()[0][0] is None:
        await message.answer(f'You have not connected the wallet if the bot has not written to you, you should start a dialogue with @{bot_username} and re-send /reg')
        await bot.send_message(chat_id=message.from_user.id, text="Connect your wallet (Tonkeeper or Tonhub)🚀", reply_markup=kb.Walletkb)
    await message.delete()

@dp.message_handler(state = States.AddAdmin, chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def check_to_add_admin(message: types.Message, state: FSMContext):
    if message['reply_to_message'] is None or not (message['reply_to_message']['from']['id'] == bot_id):
        return
    await state.finish()
    if ('@' not in message.text):
        await message.answer("incorrectly entered a username ❌")
        return
    username = re.search(r'@(\w+)', message.text).string[1::]

    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]

    if message.from_user.id != owner_id:
        return

    for member in cur.execute(f"SELECT user_id FROM Members WHERE chat_id == '{chat_id}'").fetchall():
        user = await bot.get_chat_member(message.chat.id, cur.execute(f"SELECT id_tg FROM Users WHERE id == {member[0]}").fetchall()[0][0])
        if (user.user.username != cur.execute(f"SELECT username FROM Users WHERE id_tg == {user.user.id}").fetchall()[0][0]):
            cur.execute(f"UPDATE Users SET username = '{user.user.username}' WHERE id_tg = {user.user.id}")
            con.commit()

    id = cur.execute(f"SELECT id FROM Users WHERE username == '{username}'").fetchall()
    id_tg = cur.execute(f"SELECT id_tg FROM Users WHERE username == '{username}'").fetchall()

    if id_tg and id_tg == owner_id:
        await message.answer("This user is the owner ❌")
    elif id:
        if not cur.execute(f"SELECT id_users FROM Admins WHERE id_users == {id[0][0]} AND chat_id == {chat_id}").fetchall():
            cur.execute(f"INSERT INTO Admins (id_users, chat_id) VALUES ({id[0][0]}, {chat_id})")
            con.commit()
            await message.answer("The user is assigned as an admin ✅")
        else: 
            await message.answer("This user is already an admin ⚠️")
    else:
        await message.answer("This user not registered (he can try write /reg) or incorrectly entered a username ❌")

@dp.message_handler(state = States.RemoveAdmin, chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def check_to_remove_admin(message: types.Message, state: FSMContext):
    if message['reply_to_message'] is None or not (message['reply_to_message']['from']['id'] == bot_id):
        return
    await state.finish()
    if ('@' not in message.text):
        await message.answer("incorrectly entered a username ❌")
        return
    username = re.search(r'@(\w+)', message.text).string[1::]

    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    id = cur.execute(f"SELECT id FROM Users WHERE username == '{username}'").fetchall()
    id_tg = cur.execute(f"SELECT id_tg FROM Users WHERE username == '{username}'").fetchall()[0][0]

    if message.from_user.id != owner_id:
        return

    for member in cur.execute(f"SELECT user_id FROM Members WHERE chat_id == '{chat_id}'").fetchall():
        user = await bot.get_chat_member(message.chat.id, cur.execute(f"SELECT id_tg FROM Users WHERE id == {member[0]}").fetchall()[0][0])
        if (user.user.username != cur.execute(f"SELECT username FROM Users WHERE id_tg == {user.user.id}").fetchall()[0][0]):
            cur.execute(f"UPDATE Users SET username = '{user.user.username}' WHERE id_tg = {user.user.id}")
            con.commit()

    if id_tg and id_tg == owner_id:
        await message.answer("This user is the owner ❌")
    elif id:
        if cur.execute(f"SELECT id_users FROM Admins WHERE id_users == {id[0][0]} AND chat_id == {chat_id}").fetchall():
            cur.execute(f"DELETE from Admins where id_users == {id[0][0]} AND chat_id == {chat_id}")
            con.commit()
            await message.answer("The user has been removed from the admin position ✅")
        else: 
            await message.answer("This user is not an admin ⚠️")
    else:
        await message.answer("This user not registr or incorrectly entered a username ❌")

@dp.message_handler(state = States.AddNFT, chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def check_to_add_nft(message: types.Message, state: FSMContext):
    if message['reply_to_message'] is None or not (message['reply_to_message']['from']['id'] == bot_id):
        return
    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    admins = cur.execute(f"SELECT id_users FROM Admins WHERE chat_id == {chat_id}").fetchall()
    await state.finish()

    users = []
    for adm in admins:
        users.append(cur.execute(f"SELECT id_tg FROM Users WHERE id == {adm[0]}").fetchall()[0][0])
    users.append(owner_id)

    if message.from_user.id in users:
        collection_address = message.text
        if not cur.execute(f"SELECT chat_id FROM Passes WHERE collection_address == '{collection_address}' AND chat_id == {chat_id}").fetchall():
            url = f'https://tonapi.io/v2/nfts/collections/{collection_address}'
            try:
                response = requests.get(url).json()
            except:
                await message.answer("something went wrong, try again later...")
                return
            if 'error' in response:
                await message.answer('Invalid or non-existent address ❌')
                return
            chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
            cur.execute(f"INSERT INTO Passes (chat_id, collection_address) VALUES ({chat_id}, '{collection_address}')")
            con.commit()
            await message.answer('NFT successfully added ✅')
        else:
            await message.answer('This address has already been added ⚠️')

@dp.message_handler(state = States.RemoveNFT, chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def check_to_remove_nft(message: types.Message, state: FSMContext):
    if message['reply_to_message'] is None or not (message['reply_to_message']['from']['id'] == bot_id):
        return
    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    admins = cur.execute(f"SELECT id_users FROM Admins WHERE chat_id == {chat_id}").fetchall()
    await state.finish()

    users = []
    for adm in admins:
        users.append(cur.execute(f"SELECT id_tg FROM Users WHERE id == {adm[0]}").fetchall()[0][0])
    users.append(owner_id)

    if message.from_user.id in users:
        collection_address = message.text
        if cur.execute(f"SELECT chat_id FROM Passes WHERE collection_address == '{collection_address}'").fetchall():
            chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
            cur.execute(f"DELETE FROM Passes WHERE chat_id == {chat_id} AND collection_address == '{collection_address}'")
            con.commit()
            await message.answer('Address successfully removed ✅')
        else:
            await message.answer('This address was not added ⚠️')

async def check_users_in_chats():
    members = cur.execute(f"SELECT * FROM Members").fetchall()
    for member in members:
        address = cur.execute(f"SELECT address FROM Users WHERE id == {member[0]}").fetchall()[0][0]
        if address is None:
            user_id = cur.execute(f"SELECT id_tg FROM Users WHERE id == {member[0]}").fetchall()[0][0]
            chat_id = cur.execute(f"SELECT id_tg FROM Chats WHERE id == {member[1]}").fetchall()[0][0]
            if await bot.ban_chat_member(chat_id, user_id):
                await bot.unban_chat_member(chat_id, user_id)
                cur.execute(f"DELETE FROM Admins WHERE id_users == {user_id} AND chat_id == {chat_id}")
                con.commit()
                cur.execute(f"DELETE FROM Members WHERE user_id == {user_id} AND chat_id == {chat_id}")
                con.commit()
            continue
        chat_id = member[1]
        i = 0
        nfts = cur.execute(f"SELECT collection_address FROM Passes WHERE chat_id == {chat_id}").fetchall()
        while i < len(nfts):
            url = f'https://tonapi.io/v2/accounts/{address}/nfts?collection={nfts[i]}&limit=1000&offset=0&indirect_ownership=false'
            try:
                response = requests.get(url).json()
            except:
                continue
            if response:
                return
            else:
                i += 1
        user_id = cur.execute(f"SELECT id_tg FROM Users WHERE id == {member[0]}").fetchall()[0][0]
        chat_id = cur.execute(f"SELECT id_tg FROM Chats WHERE id == {member[1]}").fetchall()[0][0]
        if await bot.ban_chat_member(chat_id, user_id):
            await bot.unban_chat_member(chat_id, user_id)
            cur.execute(f"DELETE FROM Admins WHERE id_users == {user_id} AND chat_id == {chat_id}")
            con.commit()
            cur.execute(f"DELETE FROM Members WHERE user_id == {user_id} AND chat_id == {chat_id}")
            con.commit()

@dp.message_handler(state = '*', commands=['start'], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE])
async def start_command(message: types.Message):
    await message.answer("The Access Control Bot is a specialized bot that utilizes NTFs (Non Fungible Tokens) or SBTs to manage access to your Telegram groups. This comfortable solution allows you to control who has access to your groups and when, with NFTs/SBTs as unique, non-transferable identifiers for each member.")

@dp.message_handler(commands = ['help'], state = '*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP, types.ChatType.PRIVATE])
async def help_instructions(message: types.Message, state: FSMContext):
    await message.answer("1\. To get started, add the bot to your group\! It's as easy as inviting a new member\. Look for the bot by its username and add it\.\n2\. Next, make sure you give the bot the necessary powers to perform its tasks\. You can do this by promoting the bot to an administrator role in your group settings\.\n3\. Write the /add\_nft command in the group and reply to the bot's message with the address of the collection\.\n\nYour bot should now be up and running smoothly\.\n\nWe're here to help you at every step\. If you run into any issues or need help understanding anything about the bot's functionalities, don't hesitate to reach out to @Andreyburnosov\.\n\nFor more detailed guidance, you might also want to check out our 'Access control bot' guide on GitHub\. Here's the link to the readme: [Access control bot](https://github.com/AndreyBurnosov/Access_control_bot)", parse_mode='MarkdownV2', disable_web_page_preview=True)
@dp.message_handler(state = '*', chat_type=types.ChatType.PRIVATE)
async def unknown_command(message: types.Message):
    await message.answer("Unknown command ⚠️\nMost commands are intended for use in a group.")

if __name__ == '__main__':
    scheduler.add_job(check_users_in_chats, "interval", minutes=10)
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
