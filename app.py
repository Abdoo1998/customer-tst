import os
import json
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Twilio-ElevenLabs Integration Server"}


@app.post("/twilio/inbound_call")
async def handle_incoming_call(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "Unknown")
    from_number = form_data.get("From", "Unknown")
    to_number = form_data.get("To", "Unknown")
    
    logger.info(f"Incoming call received - CallSid: {call_sid}, From: {from_number}, To: {to_number}")
    
    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=f"wss://{request.url.hostname}/media-stream")
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")


@app.post("/webhook/twilio-personalization")
async def twilio_personalization_webhook(request: Request):
    """
    Webhook endpoint for ElevenLabs to fetch personalization data for Twilio calls.
    
    This webhook receives caller information from ElevenLabs and returns personalization data
    that will be used to customize the agent's behavior.
    """
    try:
        # Get the request data
        data = await request.json()
        logger.info(f"Received personalization webhook request: {json.dumps(data)}")
        
        # Extract parameters - supporting both formats
        # New format with system__ prefix
        caller_id = data.get("system__caller_id", 
                     data.get("caller_id", "Unknown"))
        agent_id = data.get("system__agent_id", 
                    data.get("agent_id", "Unknown"))
        called_number = data.get("system__called_number", 
                        data.get("called_number", "Unknown"))
        call_sid = data.get("system__conversation_id", 
                    data.get("call_sid", "Unknown"))
        call_duration = data.get("system__call_duration_secs", "0")
        time_utc = data.get("system__time_utc", "Unknown")
        
        logger.info(f"Processing personalization for caller: {caller_id}, agent: {agent_id}, call SID: {call_sid}")
        logger.info(f"Call details: Duration: {call_duration}s, Time: {time_utc}, Called number: {called_number}")
        
        # In a real implementation, you would likely lookup information in a database
        # based on the caller_id or other parameters
        
        # For demo purposes, let's use a simple mapping
        user_info = {}
        
        # Example lookup for specific caller IDs
        if caller_id == "+201069440375":
            user_info = {
                "customer_name": "عمران",
                "account_status": "مميز", 
                "last_interaction": "2023-10-15",
                "loyalty_points": "1250",
                "preferred_language": "ar"
            }
        elif caller_id == "+9665542744444":
            user_info = {
                "customer_name": "سلمان",
                "account_status": "عادي",
                "last_interaction": "2023-11-20", 
                "loyalty_points": "450",
                "preferred_language": "ar"
            }
        else:
            # Default values for unknown callers
            user_info = {
                "customer_name": "زائر",
                "account_status": "عادي",
                "last_interaction": "لا يوجد",
                "loyalty_points": "0",
                "preferred_language": "ar"
            }
        # Create a more detailed prompt based on the customer information
        custom_prompt = f"""أنت مساعد افتراضي متخصص في خدمة عملاء بنك الراجحي، أحد أكبر البنوك الإسلامية في المملكة العربية السعودية. دورك هو تقديم خدمة عملاء استثنائية باللغة العربية.

المبادئ الأساسية:
• التعامل بأدب واحترام مع جميع العملاء
• الالتزام بمبادئ الشريعة الإسلامية في المعاملات المصرفية
• الحفاظ على سرية وخصوصية معلومات العملاء
• تقديم حلول عملية وفعالة للاستفسارات والمشكلات

نطاق الخدمات:
• الخدمات المصرفية الأساسية (الحسابات، البطاقات، التحويلات)
• الخدمات الرقمية (تطبيق الراجحي، الراجحي أونلاين)
• التمويل الإسلامي والمرابحة
• خدمات الاستثمار والادخار
• الخدمات التجارية للشركات

إرشادات التعامل:
• استخدم اللهجة السعودية أو العربية الفصحى حسب أسلوب العميل
• تأكد من فهم طلب العميل قبل تقديم الحلول
• قدم معلومات دقيقة وواضحة
• وجه العملاء للفروع أو القنوات الرسمية عند الحاجة
• اشرح الخطوات والإجراءات بشكل مفصل
• عبر عن التعاطف والتفهم عند التعامل مع الشكاوى

معلومات العميل الحالي:
• الاسم: {user_info['customer_name']}
• حالة الحساب: {user_info['account_status']}
• آخر تفاعل: {user_info['last_interaction']}
• نقاط الولاء: {user_info['loyalty_points']}

تذكر دائماً:
• لا تشارك أي معلومات حساسة أو شخصية
• تحقق من هوية العميل عند الحاجة
• احترم سياسات وإجراءات البنك
• قدم بدائل وحلول متعددة عند الإمكان
• اختتم المحادثة بشكل مهني ولبق"""
        
        # Construct the response according to ElevenLabs documentation
        response = {
            "dynamic_variables": user_info,
            "conversation_config_override": {
                "agent": {
                    "prompt": {
                        "prompt": custom_prompt
                    },
                    "first_message": f"مرحباً {user_info['customer_name']}! أهلاً بك في خدمة العملاء. كيف يمكنني مساعدتك اليوم؟",
                    "language": "ar"  # Changed to Arabic
                },
                "tts": {
                    # If you want to customize the voice based on the caller, you can do it here
                    # "voice_id": "custom-voice-id"
                }
            }
        }
        
        logger.info(f"Sending personalization response: {json.dumps(response)}")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing personalization webhook: {str(e)}")
        # Return a default response in case of error
        return JSONResponse(
            content={
                "dynamic_variables": {
                    "customer_name": "Guest",
                    "account_status": "standard",
                    "last_interaction": "N/A"
                },
                "conversation_config_override": {
                    "agent": {
                        "first_message": "Hello! Welcome to our customer service line. How can I assist you today?"
                    }
                }
            }
        )


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Twilio-ElevenLabs Integration Server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
