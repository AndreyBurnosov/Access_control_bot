# How to run Access control bot

## 👋 Introduction

This bot will help you set up access to your group via NFT

## 🤖 creating a bot

Create a bot in [BotFather](https://t.me/BotFather), then take the token and paste it into the appropriate field in the file [config.py](https://github.com/AndreyBur/Access_control_bot/blob/master/config_example.py) and also insert your bot's id in the corresponding field.

### ⚙️ Setting up the bot

Set up in [BotFather](https://t.me/BotFather) > `Edit Bot` > `Edit Commands` and we write this:

```bash
add_admin - add an admin to manage NFT
remove_admin - remove admin
add_nft - add an NFT for access to the group
remove_nft - remove NFT
show_nft - show all the NFT for access to this group
help - if you have any problems with bot
```

## 🖥 Running Access control bot

1.  Before launching this bot, you need to download all the necessary libraries:

```bash
aiogram==2.25.1
pytonconnect==0.1.1
qrcode==7.4.2
requests==2.28.2
tonsdk==1.0.12
```

2.  Then clone the repository:

```bash
git clone https://github.com/AndreyBur/Access_control_bot
```

3.  Сreate a group and add a bot there

####That's all, you can run the bot

## 📌 References

- Author: [Andrew Burnosov](https://github.com/AndreyBur) (TG: [@AndrewBurnosov](https://t.me/AndreyBurnosov))

Developed for footsteps Developed for footsteps [#215](https://github.com/ton-society/ton-footsteps/issues/215) from TON Footsteps.
