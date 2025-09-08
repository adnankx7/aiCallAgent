# 📞 DrivePK Voice Assistant

This is a real-time voice assistant system that I built using **FastAPI**, **Twilio**, and **OpenAI's GPT-4o**. It automatically calls users who list their vehicles for sale and promotes premium ad services through a natural, Urdu-language conversation.

## ✅ What I Have Built

- 🔍 **Listing Monitor**: Watches a `listings.json` file for new vehicle listings.
- 📞 **Automated Calling**: When a new listing is detected, it triggers a call to the seller using **Twilio Voice API**.
- 🧠 **AI-Powered Conversations**: Integrates with **OpenAI GPT-4o Realtime** to handle live, two-way conversations in **Urdu**, representing a virtual assistant named **Sara**.
- 🗣️ **Ad Promotion in Urdu**: The assistant introduces sellers to **Featured Ad** plans with a polite, persuasive tone.
- 🧾 **Conversation Logging**: Saves every conversation in a structured format (JSON) under the `call_logs/` folder for future reference.
- 🔁 **Real-Time Media Streaming**: Handles bi-directional streaming between Twilio ↔ FastAPI ↔ OpenAI using WebSockets.
- 🔐 **Environment-based Configuration**: Secure and flexible setup using `.env` for API keys and settings.

## 🧰 Technologies Used

- **FastAPI** – Web framework
- **Twilio** – Voice calls and media streaming
- **OpenAI GPT-4o** – Real-time AI conversation
- **Watchdog** – File system monitoring
- **HTTPX** – Async HTTP client
- **WebSockets** – Real-time data streaming
- **Python AsyncIO** – For concurrent processing

## 🔧 How It Works

1. A seller lists a car and their phone number is added to `listings.json`.
2. My app detects the new listing and initiates a voice call.
3. Twilio streams the call audio to my backend.
4. My backend forwards the audio to GPT-4o in real time.
5. GPT-4o replies with audio in Urdu, promoting DrivePK's ad features.
6. The entire conversation is logged.

## 📂 Project Structure

- `app.py` – Main FastAPI app with call handling and WebSocket integration
- `file_monitor.py` – Monitors `listings.json` and triggers calls
- `feature_ads.txt` – Contains the ad plans used in the sales pitch
- `call_logs/` – Logs of all conversations
- `.env` – Configuration file (not committed)

## 💬 Language Support

- Entire assistant conversation is handled in **Urdu**, with clear, friendly, and persuasive language.

## 🚀 How to Run

1. Clone the repository.
2. Set up your `.env` file with Twilio, OpenAI, and NGROK details.
3. Add your ad content to `feature_ads.txt`.
4. Start the app:

```
OPENAI_API_KEY = "sk-proj-ydqf6......"
NGROK_URL="NGROK_URL"
TWILIO_ACCOUNT_SID="AC731f1......."
TWILIO_AUTH_TOKEN="2a408......"
TWILIO_PHONE_NUMBER="+157......"
```

```bash
python main.py
```