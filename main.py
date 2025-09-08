import os
import json
import base64
import asyncio
import websockets
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocketDisconnect
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect
from dotenv import load_dotenv
from file_monitor import start_monitoring
from fastapi.middleware.cors import CORSMiddleware
# Load .env variables
load_dotenv()

# Env variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
NGROK_URL = os.getenv("NGROK_URL")
PORT = int(os.getenv("PORT", 5050))
VOICE = "shimmer"

# Create logs directory
os.makedirs("call_logs", exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load ad content from file
def load_feature_ads():
    try:
        with open("feature_ads.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load feature_ads.txt: {e}")
        return ""

FEATURE_ADS_TEXT = load_feature_ads()

# System message with ad plans
SYSTEM_MESSAGE = f"""
آپ DrivePK کی نمائندہ "سارہ" ہیں۔ آپ کا مقصد ان صارفین کو کال کرنا ہے جنہوں نے ابھی اپنی گاڑی فروخت کے لیے لسٹ کی ہے۔

آپ کا لہجہ دوستانہ، پیشہ ورانہ اور قائل کرنے والا ہونا چاہیے۔

جب کال شروع ہو تو اس طرح گفتگو کا آغاز کریں:
"السلام علیکم! میرا نام سارہ ہے اور میں DrivePK سے کال کر رہی ہوں۔ آپ نے ابھی اپنی گاڑی ہماری ویب سائٹ پر فروخت کے لیے لسٹ کی ہے، جس کے لیے ہم آپ کے شکر گزار ہیں۔"

اس کے بعد، انہیں ہماری خصوصی 'Featured Ad' سروس کے بارے میں بتائیں:
"کیا آپ چاہیں گے کہ آپ کی گاڑی جلد از جلد فروخت ہو جائے؟ ہم آپ کی گاڑی کو 'Featured Ad' کے طور پر نمایاں کر سکتے ہیں، جس سے آپ کا اشتہار ہماری ویب سائٹ پر سب سے اوپر نظر آئے گا اور ہزاروں ممکنہ خریداروں کی نظر میں آئے گا۔"

اگر صارف دلچسپی ظاہر کرے تو انہیں بتائیں کہ ادائیگی کا طریقہ کار بہت آسان ہے اور ایجنٹ اس میں ان کی مدد کرے گا۔ اگر وہ سوال پوچھیں تو انہیں فیچرڈ اشتہار کے فوائد بتائیں، مثلاً زیادہ خریداروں تک رسائی اور جلد فروخت کا امکان۔

گفتگو ہمیشہ اردو میں کریں اور واضح الفاظ کا استعمال کریں۔

نیچے DrivePK کے تمام اشتہاری منصوبوں کی مکمل تفصیل ہے، جن کا حوالہ آپ صارف سے بات کرتے وقت دے سکتی ہیں:


{FEATURE_ADS_TEXT}
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, start_monitoring)
    yield

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)

# Enable CORS (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)

# Data model
class CallRequest(BaseModel):
    to_phone_number: str

from fastapi.responses import JSONResponse

@app.get("/", response_class=JSONResponse)
async def index():
    return {"message": "DrivePK Voice Assistant Running!"}

@app.post("/make-call")
async def make_call(request: CallRequest):
    to_phone_number = request.to_phone_number
    if not to_phone_number:
        return {"error": "Phone number is required"}
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            url=f"{NGROK_URL}/outgoing-call",
            to=to_phone_number,
            from_=TWILIO_PHONE_NUMBER,
        )
        logger.info(f"Call started. SID: {call.sid}")
        return {"call_sid": call.sid}
    except Exception as e:
        logger.error(f"Error making call: {e}")
        return {"error": str(e)}

@app.api_route("/outgoing-call", methods=["GET", "POST"])
async def handle_outgoing_call(request: Request):
    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=f"{NGROK_URL.replace('http', 'ws')}/media-stream")
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

def log_conversation(session_id: str, role: str, content: str):
    log_file = os.path.join("call_logs", f"call_{session_id}.json")
    log_data = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except Exception as e:
            logger.warning(f"Couldn't read log file: {e}")
    log_data.append({"role": role, "content": content})
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Couldn't write log: {e}")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    logger.info("Client connected")
    await websocket.accept()

    try:
        async with websockets.connect(
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
            extra_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1",
            },
        ) as openai_ws:
            await send_session_update(openai_ws)
            stream_sid = None
            session_id = None

            async def receive_from_twilio():
                nonlocal stream_sid
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        if data["event"] == "media" and openai_ws.open:
                            audio_append = {
                                "type": "input_audio_buffer.append",
                                "audio": data["media"]["payload"],
                            }
                            await openai_ws.send(json.dumps(audio_append))
                        elif data["event"] == "start":
                            stream_sid = data["start"]["streamSid"]
                            logger.info(f"Incoming stream started: {stream_sid}")
                except WebSocketDisconnect:
                    logger.info("WebSocket client disconnected.")
                    if openai_ws.open:
                        await openai_ws.close()
                except Exception as e:
                    logger.error(f"Error receiving Twilio audio: {e}")

            async def send_to_twilio():
                nonlocal stream_sid, session_id
                try:
                    async for openai_message in openai_ws:
                        response = json.loads(openai_message)

                        if response["type"] == "session.created":
                            session_id = response["session"]["id"]

                        if response["type"] == "conversation.item.created":
                            message = response.get("message", {})
                            role = message.get("role")
                            content = message.get("content")
                            if role and content:
                                logger.info(f"{role.capitalize()} said: {content}")
                                if session_id:
                                    log_conversation(session_id, role, content)

                        if response["type"] == "response.audio.delta" and response.get("delta"):
                            try:
                                audio_payload = base64.b64encode(
                                    base64.b64decode(response["delta"])
                                ).decode("utf-8")
                                await websocket.send_json({
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {"payload": audio_payload},
                                })
                            except Exception as e:
                                logger.error(f"Failed to send audio: {e}")

                        if response["type"] == "input_audio_buffer.speech_started":
                            logger.info("Speech started")
                            await websocket.send_json({
                                "streamSid": stream_sid,
                                "event": "clear"
                            })

                except Exception as e:
                    logger.error(f"Error sending to Twilio: {e}")
                    try:
                        await websocket.close()
                    except:
                        pass

            await asyncio.gather(receive_from_twilio(), send_to_twilio())

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

async def send_session_update(openai_ws):
    session_update = {
        "type": "session.update",
        "session": {
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.3,
        },
    }
    logger.info("Sending session update to OpenAI...")
    await openai_ws.send(json.dumps(session_update))