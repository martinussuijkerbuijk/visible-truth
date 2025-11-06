import asyncio
from telethon import TelegramClient

#
# IMPORTANT: RUN THIS SCRIPT ONCE FROM YOUR TERMINAL TO LOG IN
#
#   1. Run: python create_session.py
#   2. Enter your API ID, Hash, and Phone Number.
#   3. Enter the login code Telegram sends you.
#
# This will create a 'journalist_session.session' file.
# The main web app (app.py) NEEDS this file to run.
#

async def main():
    print("--- One-Time Session Creator ---")
    print("This will create a 'journalist_session.session' file for the web app.")
    
    try:
        api_id = int(input("Enter your API ID: "))
        api_hash = input("Enter your API Hash: ")
        phone = input("Enter your Phone Number (with +country code): ")

        client = TelegramClient(
            'journalist_session', 
            api_id, 
            api_hash,
            system_version="4.16.30-CUSTOM"
        )

        print(f"Connecting as {phone}...")
        await client.start(phone=phone)
        
        print("\nSuccess! Client is authorized.")
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} {me.last_name} (@{me.username})")
        
        await client.disconnect()
        print("\nSession file 'journalist_session.session' has been created.")
        print("You can now run the main web app: python app.py")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please try again.")

if __name__ == "__main__":
    asyncio.run(main())