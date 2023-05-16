import json
import sqlite3
import re
import asyncio
import KeyBoards as kb
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.markdown import link
from datetime import datetime
from tonsdk.utils import Address
from pytonconnect import TonConnect
from pytonconnect.exceptions import UserRejectsError
from config import api_token

class States(StatesGroup):
    AddAdmin = State()
    RemoveAdmin = State()
    AddNFT = State() 


con = sqlite3.connect("DB.db", check_same_thread=False)
cur = con.cursor()

bot = Bot(token=api_token)
dp = Dispatcher(bot, storage=MemoryStorage())



@dp.chat_join_request_handler()
async def start1(update: types.ChatJoinRequest):
    if not cur.execute(f"SELECT id_tg FROM Users WHERE id_tg == {update.from_user.id}").fetchall():
        cur.execute(f"INSERT INTO Users (id_tg, username) VALUES ({update.from_user.id}, '{update.from_user.username}')")
        con.commit()
    if cur.execute(f"SELECT address FROM Users WHERE id_tg == {update.from_user.id}").fetchall()[0][0] is None:
        await bot.send_message(chat_id=update.from_user.id, text="To join the group, connect your wallet (Tonkeeper or Tonhub) and send the application again", reply_markup=kb.Walletkb)
    else:
        address = cur.execute(f"SELECT address FROM Users WHERE id_tg == {update.from_user.id}").fetchall()[0][0]
        url = f'https://tonapi.io/v2/accounts/{address}/nfts?limit=1000&offset=0&indirect_ownership=false'
        try:
            response = requests.get(url).json()['nft_items']
        except:
            await bot.send_message(chat_id=update.from_user.id, text="something went wrong, try again later...")
            return
        chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {update.chat.id}").fetchall()[0][0]
        nfts = []
        for i in cur.execute(f"SELECT collection_address FROM Passes WHERE chat_id == {chat_id}").fetchall():
            nfts.append(i[0])
        for nft in response:
            if nft['collection']['address'] in nfts:
                await update.approve()
                return
        await bot.send_message(chat_id=update.from_user.id, text="You don't have the necessary NFT to join the group")
        
        
        

@dp.message_handler(text = 'Tonkeeper', state='*', chat_type=types.ChatType.PRIVATE)
async def connect_wallet_tonkeeper(message: types.Message):
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/XaBbl4/pytonconnect/main/pytonconnect-manifest.json')
    is_connected = await connector.restore_connection()
    
    wallets_list = connector.get_wallets()

    generated_url_tonkeeper = await connector.connect(wallets_list[0])
    text = f'[Tonkeeper link]({generated_url_tonkeeper})'
    msg = await bot.send_message(message.from_user.id, text, parse_mode='MarkdownV2')

    flag = True
    while flag:
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                flag = False
                address = Address(connector.account.address).to_string(True, True, True)
            break
    
    await msg.delete()
    await bot.send_message(message.from_user.id, 'Your wallet has been successfully connect')
    cur.execute(f"UPDATE Users SET address = '{address}' WHERE id_tg = {message.from_user.id}")
    con.commit()

@dp.callback_query_handler(text = 'Tonhub', state='*', chat_type=types.ChatType.PRIVATE)
async def connect_wallet_tonhub(message: types.Message):
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/XaBbl4/pytonconnect/main/pytonconnect-manifest.json')
    is_connected = await connector.restore_connection()
    
    wallets_list = connector.get_wallets()

    generated_url_tonhub = await connector.connect(wallets_list[1])
    text = f'[Tonhub link]({generated_url_tonhub})'
    msg = await bot.send_message(message.from_user.id, text, parse_mode='MarkdownV2')
    msg = await message.answer(f"Tonhub Link: {text}")

    flag = True
    while flag:
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                flag = False
                address = Address(connector.account.address).to_string(True, True, True)
            break
    
    await msg.delete()
    await bot.send_message(message.from_user.id, 'Your wallet has been successfully connect')
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

@dp.message_handler(commands=['add_nft'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def add_nft(message: types.Message, state: FSMContext):
    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    admins = cur.execute(f"SELECT id_users FROM Admins WHERE chat_id == {chat_id}").fetchall()

    users = []
    for adm in admins:
        users.append(cur.execute(f"SELECT id_tg FROM Users WHERE id == {adm[0]}").fetchall()[0][0])
    users.append(owner_id) 
    
    if message.from_user.id in users:
        await message.answer('To add a new NFT for access, send colection address.\nReply for this message')
        await States.AddNFT.set()
    else: 
        await message.answer("You don't have enough permission")

@dp.message_handler(commands=['show_nft'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def add_nft(message: types.Message, state: FSMContext):
    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    admins = cur.execute(f"SELECT id_users FROM Admins WHERE chat_id == {chat_id}").fetchall()

    users = []
    for adm in admins:
        users.append(cur.execute(f"SELECT id_tg FROM Users WHERE id == {adm[0]}").fetchall()[0][0])
    users.append(owner_id) 
    
    if message.from_user.id in users:
        nfts = cur.execute(f"SELECT collection_address FROM Passes WHERE chat_id == {chat_id}").fetchall()
        text = ''
        for i in range(len(nfts)):
            text += f'{i + 1}\)' + '`' + nfts[i][0] + '`' + '\n'
        await message.answer(f'NFTs:\n{text}', parse_mode='MarkdownV2')
        await state.finish()
    else: 
        await message.answer("You don't have enough permission")

@dp.message_handler(commands=['add_admin'], state='*', chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def add_admin(message: types.Message, state: FSMContext):
    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    if message.from_user.id == owner_id:
        await message.answer('To add a new admin, send his username.\nExample: "@username"\nReply for this message')
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
    id = cur.execute(f"SELECT id FROM Users WHERE username == '{username}'").fetchall()
    id_tg = cur.execute(f"SELECT id_tg FROM Users WHERE username == '{username}'").fetchall()

    if message.from_user.id != owner_id:
        return

    if id_tg and id_tg == owner_id:
        await message.answer("This user is the owner")
    elif id:
        if not cur.execute(f"SELECT id_users FROM Admins WHERE id_users == {id[0][0]} AND chat_id == {chat_id}").fetchall():
            cur.execute(f"INSERT INTO Admins (id_users, chat_id) VALUES ({id[0][0]}, {chat_id})")
            con.commit()
            await message.answer("The user is assigned as an admin")
            await state.finish()
        else: 
            await message.answer("This user is already an admin")
    else:
        await message.answer("This user not registr or incorrectly entered a username")

@dp.message_handler(state = States.RemoveAdmin, chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def check_to_remove_admin(message: types.Message, state: FSMContext):
    if ('@' not in message.text):
        await message.answer("incorrectly entered a username")
        return
    username = re.search(r'@(\w+)', message.text).string[1::]

    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    id = cur.execute(f"SELECT id FROM Users WHERE username == '{username}'").fetchall()
    id_tg = cur.execute(f"SELECT id_tg FROM Users WHERE username == '{username}'").fetchall()[0][0]

    if message.from_user.id != owner_id:
        return

    if id_tg and id_tg == owner_id:
        await message.answer("This user is the owner")
    elif id:
        if cur.execute(f"SELECT id_users FROM Admins WHERE id_users == {id[0][0]} AND chat_id == {chat_id}").fetchall():
            cur.execute(f"DELETE from Admins where id_users == {id[0][0]} AND chat_id == {chat_id}")
            con.commit()
            await message.answer("The user has been removed from the admin position")
            await state.finish()
        else: 
            await message.answer("This user is not an admin")
    else:
        await message.answer("This user not registr or incorrectly entered a username")

@dp.message_handler(state = States.AddNFT, chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def check_to_add_nft(message: types.Message, state: FSMContext):
    owner_id = cur.execute(f"SELECT owner_id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
    admins = cur.execute(f"SELECT id_users FROM Admins WHERE chat_id == {chat_id}").fetchall()
    
    users = []
    for adm in admins:
        users.append(cur.execute(f"SELECT id_tg FROM Users WHERE id == {adm[0]}").fetchall()[0][0])
    users.append(owner_id)
    if message.from_user.id in users:
        collection_address = message.text
        if not cur.execute(f"SELECT chat_id FROM Passes WHERE collection_address == '{collection_address}'").fetchall():
            chat_id = cur.execute(f"SELECT id FROM Chats WHERE id_tg == {message.chat.id}").fetchall()[0][0]
            cur.execute(f"INSERT INTO Passes (chat_id, collection_address) VALUES ({chat_id}, '{collection_address}')")
            con.commit()
            await message.answer('Address successfully added')
            await state.finish()
        else:
            await message.answer('This address has already been added')


@dp.message_handler(state = '*', chat_type=types.ChatType.PRIVATE)
async def unknown_command(message: types.Message):
    await message.answer("unknown command")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)