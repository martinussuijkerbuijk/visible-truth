import asyncio
import time
from flask import Flask, render_template, request, Response
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import FloodWaitError
import json
import os
from dotenv import load_dotenv

load_dotenv()

# --- Flask App Initialization ---
app = Flask(__name__, template_folder='.', static_folder='./static', static_url_path='')

# --- Global Client Configuration ---
# Read API credentials from environment variables.
# You will set these in your Google Cloud environment.
API_ID = os.environ.get('TELEGRAM_API_ID')    
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Check if credentials are set
if not API_ID or not API_HASH:
    print("CRITICAL ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables are not set.")
    # We don't exit, but the scrape will fail, which is fine.

# This is the session file you created with create_session.py
SESSION_FILE = 'journalist_session.session'

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

async def _run_scrape(params):
    """
    The core async telethon logic.
    This will 'yield' data back to the streaming function.
    """
    yield "log:Initializing Telethon client...\n"
    
    # Check if session file exists
    if not os.path.exists(SESSION_FILE):
        yield f"log:ERROR: Server-side session file '{SESSION_FILE}' not found. The app is not configured correctly.\n"
        return

    # Use the API_ID and API_HASH from the environment variables
    if not API_ID or not API_HASH:
        yield f"log:ERROR: Server is missing API_ID/API_HASH configuration.\n"
        return

    # check for empty params ---
    if not params['channels'] or (len(params['channels']) == 1 and not params['channels'][0]):
        yield "log:ERROR: No channels were provided. Please enter at least one @username.\n"
        return
    if not params['keywords'] or (len(params['keywords']) == 1 and not params['keywords'][0]):
        yield "log:ERROR: No keywords were provided. Please enter at least one keyword.\n"
        return

    client = TelegramClient(
        SESSION_FILE, 
        int(API_ID), 
        API_HASH,
        system_version="4.16.30-CUSTOM"
    )

    try:
        yield f"log:Connecting using existing session...\n"
        await client.connect()

        if not await client.is_user_authorized():
            yield f"log:ERROR: Server session is not authorized. The 'journalist_session.session' file is invalid or expired.\n"
            await client.disconnect()
            return

        yield "log:Client connected successfully.\n"
        total_found = 0
        
        for channel in params['channels']:
            if not channel: continue
            yield f"log:\n--- Searching Channel: @{channel} ---\n"
            try:
                entity = await client.get_entity(channel)
                
                for keyword in params['keywords']:
                    if not keyword: continue
                    yield f"log:Searching for keyword: '{keyword}'...\n"
                    message_count = 0
                    
                    try:
                        async for message in client.iter_messages(
                            entity,
                            search=keyword,
                            limit=params['limit']
                        ):
                            message_count += 1
                            message_text = (message.text or "[Media Message]").replace('\n', ' ')
                            
                            # 'data:' prefix is for Server-Sent Events
                            message_data = {
                                'channel': channel,
                                'keyword': keyword,
                                'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                                'text': message_text,
                                'link': f"https://t.me/{channel}/{message.id}"
                            }
                            yield f"data:{json.dumps(message_data)}\n"

                        yield f"log:Found {message_count} messages for '{keyword}'.\n"
                        total_found += message_count

                    except FloodWaitError as e:
                        yield f"log:Flood wait error. Sleeping for {e.seconds} seconds.\n"
                        time.sleep(e.seconds)
                    except Exception as e:
                        yield f"log:Error searching for '{keyword}': {e}\n"
            
            except ValueError:
                yield f"log:Error: Could not find channel @{channel}. Skipping.\n"
            except Exception as e:
                yield f"log:An error occurred with @{channel}: {e}\n"

        yield f"log:\nFound a total of {total_found} messages.\n"
    
    except Exception as e:
        yield f"log:\n--- A critical error occurred: {e} ---\n"
        
    finally:
        await client.disconnect()
        yield "log:Client disconnected. Scrape finished.\n"
        yield "done:true\n"


# "Sync-to-Async" bridge ---
def _stream_helper(params):
    """
    A synchronous generator that bridges Flask (sync) to Telethon (async).
    It creates a new event loop and runs the async generator manually.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Get the async generator object
    gen = _run_scrape(params)
    
    try:
        while True:
            # Manually run the event loop until the next item is yielded
            # This is the async equivalent of "next(gen)"
            data = loop.run_until_complete(gen.__anext__())
            yield data
    except StopAsyncIteration:
        # The generator is finished
        pass
    except Exception as e:
        # Yield the error to the frontend
        yield f"log:Error in streaming bridge: {e}\n"
        yield "done:true\n"
    finally:
        loop.close()


@app.route('/scrape', methods=['POST'])
def scrape():
    """
    This is the main endpoint. It receives the form data and
    starts the async scrape, streaming the results back.
    """
    # Get form data
    form_data = request.json
    
    print(f"\n[SERVER LOG] Received form data: {form_data}")
    
    try:
        # We no longer get api_id or api_hash from the form.
        params = {
            "limit": int(form_data.get('limit', 100)),
            "channels": [c.strip() for c in form_data.get('channels', '').split('\n')],
            "keywords": [k.strip() for k in form_data.get('keywords', '').split('\n')]
        }
        
        print(f"[SERVER LOG] Parsed params: {params}")

    except Exception as e:
        print(f"[SERVER LOG] Error parsing params: {e}")
        return Response(f"log:Invalid input: {e}\n", mimetype='text/event-stream')

    # We now call our new synchronous "bridge" function,
    # which Flask's Response object can iterate over correctly.
    return Response(_stream_helper(params), mimetype='text/event-stream')

if __name__ == '__main__':
    print("--- Investigative Assistant ---")
    print("First, run 'python create_session.py' (if you haven't already).")
    print("This app expects 'TELEGRAM_API_ID' and 'TELEGRAM_API_HASH' environment variables.")
    print("Starting Flask server...")
    print("Open http://127.0.0.1:5000 in your browser.")
    # For cloud deployment, the host service (liwe can use Gunicorn) will run the 'app' object.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)