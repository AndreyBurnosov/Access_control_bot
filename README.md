# Guide to Running the Access Control Bot

## 👋 Introduction

The Access Control Bot is a specialized bot that utilizes NTFs (Non Fungible Tokens) or SBTs to manage access to your Telegram groups. This comfortable solution allows you to control who has access to your groups and when, with NFTs/SBTs as unique, non-transferable identifiers for each member.

## 🤖 Creating a bot

1.  Visit [BotFather](https://t.me/BotFather) on Telegram.

2.  Follow the instructions to create a new bot.

3.  Once created, BotFather will provide you with a unique token. This token is crucial as it allows your bot to communicate with the Telegram API.

4.  Copy this token and paste it into the corresponding field in the [`config.py`](https://github.com/AndreyBurnosov/Access_control_bot/blob/master/config.py) file found in your cloned repository.

5.  Additionally, insert your bot's id in the respective field in the same file with [**ID BOT**](https://t.me/myidbot) for example.

### ⚙️ Setting up the bot

To set up your bot, you need to define these commands. Here is how you can do it:

1.  Go back to [BotFather](https://t.me/BotFather).

2.  Select your bot and choose buttons in this order: `Edit Bot` > `Edit Commands`.

3.  Set up the following commands:

    - `add_admin` - This command will allow you to add a new administrator who will have the authority to manage NFTs.
    - `remove_admin` - This command allows you to remove an existing administrator.
    - `add_nft` - Use this command to add a new NFT, which will grant access to your group.
    - `remove_nft` - This command removes an existing NFT.
    - `show_nft` - Use this command to display a list of all the NFTs that can grant access to your group.
    - `reg` - This program will register users who were already in the group before being added to the bot.
    - `help` - This command will provide contact information for Telegram support if there are issues with the bot.

## 💬 Setting up the group

1.  **Create a Private Group:** To create a private group in Telegram, click on the pencil icon in the lower right corner, then select "New Group". When prompted to assign a name to the group and add members, only assign the name and skip adding any members at this stage.

2.  **Access Group Settings:** After creating the group, tap on the group name at the top of the screen. This action will take you to the group settings.

3.  **Create an Invitation Link:** Within the group settings, select the option labeled "Add Members". From the following options, choose "Invite to Group via Link", then proceed to "Manage Invite Links", and finally select "Create a New Link". This will allow you to generate a unique invitation link for your group.

4.  **Configure the Invitation Link:** Ensure to enable the "Request Admin Approval" feature. You can adjust the remaining settings according to your preferences.

#### Remember that now you need to use this link to access your group

## 🏁 Final steps

1.  Add a bot to your group! It's as simple as inviting a new member. Find the bot by its username and add it.

2.  Then make sure that you have given the bot the necessary permissions to perform its tasks. You can do this by assigning the bot the administrator role in your group settings.

3.  Write the `/add_nft` command in the group and reply to the bot's message with the address of the collection.

## 🖥 Running Access control bot

To launch your bot, follow these steps:

1.  Clone the repository:

```bash
git clone https://github.com/AndreyBurnosov/Access_control_bot
```

2.  Navigate to the cloned directory and download the required libraries. These libraries are necessary for the bot to function correctly:

```bash
pip install -r requiments.txt
```

3.  Create a new group on Telegram, add the bot to this group, and promote it to an admin. This step is important, because the bot needs administrative permissions to manage group access.

#### With these steps, your Access Control Bot is ready to run.

## 📌 References

- The bot was developed by [Andrew Burnosov](https://github.com/AndreyBurnosov) (TG: [@AndrewBurnosov](https://t.me/AndreyBurnosov))
- This development was part of the Footsteps project under TON Footsteps. More details can be found in footsteps [#215](https://github.com/ton-society/ton-footsteps/issues/215).
