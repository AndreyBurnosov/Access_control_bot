def build_bd(cur, con):
    cur.execute('''CREATE TABLE IF NOT EXISTS "Admins" (
        "id"	INTEGER,
        "id_users"	INTEGER,
        "chat_id"	INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS "Chats" (
        "id"	INTEGER,
        "id_tg"	INTEGER,
        "name"	TEXT,
        "owner_id"	INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS "Members" (
        "user_id"	INTEGER,
        "chat_id"	INTEGER
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS "Passes" (
        "chat_id"	INTEGER,
        "collection_address"	TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS "Users" (
        "id"	INTEGER,
        "id_tg"	INTEGER,
        "username"	TEXT,
        "address"	TEXT,
        PRIMARY KEY("id" AUTOINCREMENT)
    )''')

    con.commit()