# Guide to Running the Access Control Bot

## 👋 Introduction

The Access Control Bit is a specialized boat that utilizes Ntfs (Non Fungible Tokens) to manage access to your Telegram group. This comfortable solution allows you to control who has access to your group and when, with Ntfs as unique, non-transferable identifiers for each member.

## 🤖 creating a bot

1.  Visit [BotFather](https://t.me/BotFather) on Telegram.

2.  Follow the instructions to create a new bot.

3.  Once created, BotFather will provide you with a unique token. This token is crucial as it allows your bot to communicate with the Telegram API.

4.  Copy this token and paste it into the corresponding field in the config.py file found in your cloned repository.

5.  Additionally, insert your bot's id in the respective field in the same file.

### ⚙️ Setting up the bot

To set up your bot, you need to define its commands. Here is how you can do it:

1.  Go back to BotFather.

2.  Select your bot and choose Edit Bot > Edit Commands.

3.  Set up the following commands:

    - `add_admin` - This command will allow you to add a new administrator who will have the authority to manage NFTs.
    - `remove_admin` - This command allows you to remove an existing administrator.
    - `add_nft` - Use this command to add a new NFT, which will grant access to your group.
    - `remove_nft` - This command removes an existing NFT.
    - `show_nft` - Use this command to display a list of all the NFTs that can grant access to your group.
    - `help` - This command will provide contact information for Telegram support if there are issues with the bot.

## 🖥 Running Access control bot

To launch your bot, follow these steps:

1.  Clone the repository:

```bash
git clone https://github.com/AndreyBur/Access_control_bot
```

2.  Navigate to the cloned directory and download the required libraries. These libraries are necessary for the bot to function correctly:

```bash
pip install -r requiments.txt
```

3.  Create a new group on Telegram, add the bot to this group, and promote it to an admin. This step is important because the bot needs administrative permissions to manage group access.

#### With these steps, your Access Control Bot is ready to run.

## 📌 References

- The bot was developed by [Andrew Burnosov](https://github.com/AndreyBur) (TG: [@AndrewBurnosov](https://t.me/AndreyBurnosov))
- This development was part of the Footsteps project under TON Footsteps. More details can be found in footsteps [#215](https://github.com/ton-society/ton-footsteps/issues/215).
