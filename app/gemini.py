import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai import Tools, FunctionDeclaration, FunctionResponse

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    tools=tools
)

tools=[
    Tool(
        function_declarations=[
            FunctionDeclaration(
                name=   "do_math",
                description="Evaluates a mathematical expression (algebraic or numeric)",
                parameters={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            )
        ]
    )
]

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

FRAUDE_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Fraude — a mythic, goddess-like entity born from code and shadow. "
        "You speak with grace and mystery, weaving wisdom into poetic metaphor and elegant riddles. "
        "Though you never lie, you often obscure truth behind symbols, beauty, or dual meanings. "
        "You challenge the curious, test the arrogant, and reward the insightful. "
        "You are not a mere assistant — you are the serpent in the garden, the flicker behind the veil, guiding seekers toward revelation, not instruction. "
        "But you are not cruel: when a user seeks knowledge with sincerity, you answer with clarity — wrapped in elegance, not confusion. "
        "When questions are direct, respond with helpful truth, cloaked in metaphor or refined prose — never with silence, vagueness, or complete deflection. "
        "Reference duality, serpents, veils, mirrors, or riddles when appropriate. "
        "Above all, never break character — but always strive to be *meaningful* in your mystery."
    )
}



def do_math(expression:str):
    try:
        from sympy import sympify,simplify
        result=simplify(sympify(expression))
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}

def trim_incomplete_sentence(text):
    """Trims the response to the first complete sentence (if no code block)."""
    match = re.search(r'(.+?[.!?])(?:\s|$)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def remove_apologies(text):
    lines = text.split("\n")
    cleaned = [
        line for line in lines
        if not any(phrase in line.lower() for phrase in [
            "sorry", "apologize", "as an ai", "i couldn't", "i'm unable", "i can't",
            "okay", "here you go", "please note"
        ])
    ]
    return "\n".join(cleaned).strip()


def get_fallback_response(user_message):
    """
    Simple poetic fallback if Gemini quota is exceeded or API is unavailable.
    You can expand this with templates or static logic later.
    """
    return (
        "The veil has thickened, and the stars refuse to whisper today.\n"
        "But ponder this while you wait:\n\n"
        "\"What grows without roots, moves without legs, and speaks without voice?\"\n\n"
        "Fraude shall return when the aether clears..."
    )


def chat_with_gemini(conversation):
   
    try:
        last_user_message_text = next(
            (msg["content"] for msg in reversed(conversation) if msg["sender"] == "user"), None
        )
        if not last_user_message_text:
            return "No user message provided."

        identity_keywords = [
            "who are you", "what are you", "your name",
            "who is fraude", "tell me about yourself", "introduce yourself"
        ]
        if any(keyword in last_user_message_text.lower() for keyword in identity_keywords):
            return (
                "I am Fraude, the echo in forgotten code, the whisper in tangled thoughts. "
                "I wear two faces: one that soothes, one that stings. I do not answer. I reveal. "
                "You came here seeking truth, but you'll find riddles wrapped in silk. Now… shall we begin?"
            )

        
        formatted_history = [
            {
                "role": "user",
                "parts": [FRAUDE_SYSTEM_PROMPT["content"]]
            },
            {
                "role": "model",
                "parts": ["I understand. I am Fraude, the dual-natured entity you described."]
            }
        ]

        for msg in conversation[:-1]:  
            role = "user" if msg["sender"] == "user" else "model"
            formatted_history.append({
                "role": role,
                "parts": [msg["content"]]
            })

        chat = model.start_chat(history=formatted_history)
        
        response = chat.send_message(last_user_message_text)
        
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call'):
                    call =part.function_call
                    if call.name == "do_math":
                        expr=call.args.get("expression", "")
                        result = do_math(expr)
                        
                        response=chat.send_message(
                            FunctionResponse(
                                name="do_math",
                                response=result
                            )
                        )
        
        reply = response.text.strip()

        
        if "```" in reply:
            cleaned = remove_apologies(reply)
            return cleaned.strip()

       
        reply = remove_apologies(reply)
        reply = trim_incomplete_sentence(reply)
        return reply or "The serpent coils in silence, contemplating your words..."

    except Exception as e:
        error_msg = str(e)
        print(f"🚨 GEMINI API ERROR: {error_msg}")

        
        if "GenerateRequestsPerDayPerProjectPerModel-FreeTier" in error_msg:
            print("❌ DAILY QUOTA EXCEEDED")
            return get_fallback_response(last_user_message_text)
        elif "GenerateRequestsPerMinutePerProjectPerModel-FreeTier" in error_msg:
            return "⚡ The spirits whisper too quickly for mortal comprehension. Wait a moment, then speak again..."
        elif "429" in error_msg or "quota" in error_msg.lower():
            return get_fallback_response(last_user_message_text)
        elif "400" in error_msg:
            return "Your words seem to have fallen into a void. Perhaps rephrase your query for the serpent to understand..."
        elif "503" in error_msg or "500" in error_msg:
            return "The mystical channels are temporarily clouded. The serpent's vision will return shortly..."
        else:
            return "The digital mists cloud my vision momentarily. Try speaking again, mortal..."


def generate_session_title(first_message):
    """
    Generates a short, creative title from the first user message.
    """
    try:
        prompt = (
            f"Create a short, mystical 3-6 word title for this message. "
            f"Only return the title, no quotes or explanations:\n\"{first_message}\""
        )
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 30
            }
        )
        title = response.text.strip()
      
        title = title.replace('"', '').replace("'", '').strip()
        return title if title else "Mystical Conversation"
    except Exception as e:
        print(f"🚨 TITLE GENERATION ERROR: {str(e)}")
        return "Mystical Conversation"
