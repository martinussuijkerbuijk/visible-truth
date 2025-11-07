![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# Simple Instructions for a simple web app for a telegram Scraper

## initialization

### 1. install dependencies
It's a very no nonsense web app, so you only have to install two libraries by running 
```
python pip install -r requirements.txt
```

You can use a virtual environment. I use UV because it rules. Conda too slow!

### 2. Get your Telegram credentials.

Navigate to https://my.telegram.org/ and click **API development tools**
Create an app (in the url just set your github account or something like that)
This will give you an **API_ID** and **API_HASH**. keep this to yourself

Run ```python create_session_id.py```  for the first time and fill in your details.
This will create a ```journalist_sessions.session``` file where it will use your credentials for scraping etc.

After that create a ```.env``` file and put your credentials there like so: ```TELEGRAM_API_HASH = "blablablablab" TELEGRAM_API_ID = 12345678```

### 3. Run Script

Simply run 
```
python app.py
```
This will give you a link to a local server http://127.0.0.1:8080 (and public as well)
Open the link in your browser.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Acknowledgments

- Built with Flask and Telethon