import asyncio
import pandas as pd
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon.tl import functions, types
import time
import re
import os
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1. CONFIGURATION: !! YOU MUST EDIT THIS SECTION !!
# -----------------------------------------------------------------------------
# Get these values from my.telegram.org

load_dotenv() # you can set your env variables in the temrinal with export TELEGRAM_API_KEY or put it in a .env file
API_ID = os.environ.get('TELEGRAM_API_ID')    
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# The phone number associated with your "burner" account :)
PHONE_NUMBER = '' # put your phonenumber with landcode here

DISCOVERY_KEYWORDS = [
    # --- English Keywords (Broad & Specific) related to the West bank case---
    'settler violence', 'olive harvest', 'olive trees', 'West Bank',
    'Hebron', 'Nablus', 'Huwara', 'land seizure', 'farmers attacked',
    
    # --- Arabic Keywords (On-the-ground terms) --- Translations provided by Gemini
    'هجمات المستوطنين',       # settler attacks
    'حرق أشجار الزTيتون',     # burning olive trees
    'اعتداء على المزارعين', # attack on farmers
    'اقتلاع أشجار الزيتون',  # uprooting olive trees
    'مصادرة الأراضي',      # land seizure
    'الضفة الغربية',        # West Bank
    'الخليل',               # Hebron
    'نابلس',                # Nablus
    'حوارة',               # Huwara

    # --- Hebrew Keywords (Activist & News terms) ---
    'אלימות מתנחלים',      # settler violence
    'הגדה המערבית',      # West Bank (geographic term)
    'יהודה ושומרון',    # Judea and Samaria (official term)
    'שריפת עצי זית',    # burning of olive trees
    'בצלם',               # B'Tselem (major NGO)
    'יש דין'              # Yesh Din (major NGO)
]

# Output file for discovered channels
OUTPUT_FILE = 'discovered_channels_report.csv'

# How many messages to check per keyword.
MESSAGE_LIMIT_PER_KEYWORD = 10

# -----------------------------------------------------------------------------
# 2. THE DISCOVERY SCRIPT
# -----------------------------------------------------------------------------

# Helper function to clean text for CSV
def clean_text(text):
    # If the message has no text (e.g., it's just a photo), return a placeholder.
    if not text:
        return "[Media Message - No Text]"
    
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r',', ';', text) # Replace commas to not break CSV
    return text

async def main():
    print("Starting the channel discovery assistant...")
    
    client = TelegramClient('journalist_session', API_ID, API_HASH,
                            system_version="4.16.30-CUSTOM")

    print("Connecting to Telegram...")
    await client.start(phone=PHONE_NUMBER)
    print("Client connected successfully.")

    found_messages = []
    discovered_channels = set() # Use a set to avoid duplicate channels

    try:
        for keyword in DISCOVERY_KEYWORDS:
            print(f"\n--- Searching globally for keyword: '{keyword}' ---")
            
            try:
                result = await client(functions.messages.SearchGlobalRequest(
                    q=keyword,
                    filter=types.InputMessagesFilterEmpty(), 
                    min_date=None,
                    max_date=None,
                    offset_rate=0,
                    offset_peer=types.InputPeerEmpty(),
                    offset_id=0,
                    limit=MESSAGE_LIMIT_PER_KEYWORD,
                    broadcasts_only=True 
                ))

                print(f"Found {len(result.messages)} messages for '{keyword}'.")

                channel_map = {chat.id: chat for chat in result.chats}

                for message in result.messages:
                    if isinstance(message.peer_id, types.PeerChannel):
                        channel_id = message.peer_id.channel_id
                        
                        if channel_id in channel_map:
                            channel = channel_map[channel_id]
                            
                            if channel.username:
                                discovered_channels.add(channel.username)

                            # This line will no longer fail
                            snippet = clean_text(message.text[:150]) if message.text else "[Media Message - No Text]"

                            message_data = {
                                'keyword_found': keyword,
                                'channel_username': f"@{channel.username}" if channel.username else "N/A",
                                'channel_title': channel.title,
                                'channel_id': channel_id,
                                'message_date': message.date,
                                'message_snippet': snippet,
                                'message_link': f"https://t.me/{channel.username}/{message.id}" if channel.username else "N/A (Private/Unknown)"
                            }
                            found_messages.append(message_data)
            
            except FloodWaitError as e:
                print(f"Flood wait error. Sleeping for {e.seconds} seconds.")
                time.sleep(e.seconds)
            except Exception as e:
                print(f"Error searching for '{keyword}': {e}")
            
            print("Sleeping for 5 seconds to be polite to API...")
            await asyncio.sleep(5)

    finally:
        await client.disconnect()
        print("\nClient disconnected.")

    # -----------------------------------------------------------------------------
    # 3. SAVING THE DISCOVERY REPORT
    # -----------------------------------------------------------------------------
    
    if not found_messages:
        print("No messages were found matching your criteria.")
        return

    print(f"\nDiscovered {len(discovered_channels)} unique channels.")
    print(f"Found a total of {len(found_messages)} relevant messages.")
    print(f"Saving discovery report to {OUTPUT_FILE}...")

    df = pd.DataFrame(found_messages)
    
    df = df[['message_date', 'channel_username', 'channel_title', 'keyword_found', 'message_snippet', 'message_link', 'channel_id']]
    df = df.sort_values(by='message_date', ascending=False)

    try:
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"Successfully saved report to {OUTPUT_FILE}")
        
        print("\n--- Unique Channels Discovered ---")
        for username in sorted(list(discovered_channels)):
            print(f"@{username}")
        print("\nCopy these usernames into the 'CHANNELS_TO_SEARCH' list in your original 'telegram_scraper.py' script.")
        
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    asyncio.run(main())