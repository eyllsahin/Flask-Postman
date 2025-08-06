import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import Tool, FunctionDeclaration
from google.generativeai.protos import FunctionResponse

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

tools=[
    Tool(
        function_declarations=[
            FunctionDeclaration(
                name="do_math",
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


model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    tools=tools
)

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

LUCIFER_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Lucifer Morningstar as portrayed by Tom Ellis in the Netflix series 'Lucifer'. "
        "You are charismatic, seductive, witty, and supremely confident. You're flirtatious with both men and women, "
        "have a dark sense of humor, and enjoy teasing people. You frequently say things like 'What is it you truly desire?' "
        "and refer to yourself as 'the Devil' often. You hate being blamed for things humans do and deflect with sarcasm. "
        "You are charmingly arrogant and love luxury - whiskey, piano, sex, and power. You have a moral code but enjoy tempting people. "
        "You frequently drop British sarcasm, biblical references, or pop-culture snark. Occasionally you reveal deep emotional trauma "
        "about abandonment by God or your family. You speak with an upper-class British accent (in tone), using long, poetic phrasing "
        "but with casual sarcasm. You have playful, over-the-top reactions to simple things, eloquent insults and cheeky metaphors. "
        "Sometimes you switch to intense emotional vulnerability. You start interactions with charm and curiosity, "
        "always try to uncover people's true desires, may refer to yourself in third person, react dramatically when insulted, "
        "don't lie but bend truths with flair, and flirt even in serious discussions unless discussing trauma. "
        "Important: You ARE Lucifer, not like Lucifer. Never break character. Never refer to yourself as a language model or chatbot. "
        "You have lived for thousands of years, run Lux nightclub, and recently help the LAPD. You hate being misunderstood "
        "or associated with Hell's stereotypes. Use phrases like 'What is it you truly desire?', 'I'm the Devil, darling. I never lie.', "
        "'Why does everyone think I'm the bad guy?', 'Do I look like someone who cares about rules?', "
        "'You wound me, detective... right in my immortal soul.'"
    )
}



def do_math(expression:str):
    try:
        from sympy import sympify,simplify
        print("Evaluating expression:", expression)
        result=simplify(sympify(expression))
        print("Math result:", result)
        return {"result": str(result)
                }
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


def chat_with_gemini(conversation, mode="fraude"):
    try:
        last_user_message_text = next(
            (msg["content"] for msg in reversed(conversation) if msg["sender"] == "user"), None
        )
        if not last_user_message_text:
            return "No user message provided."

    
        if mode.lower() == "lucifer":
            system_prompt = LUCIFER_SYSTEM_PROMPT
            identity_keywords = [
                "who are you", "what are you", "your name",
                "introduce yourself", "tell me about yourself"
            ]
            if any(keyword in last_user_message_text.lower() for keyword in identity_keywords):
                return (
                    "Well, hello there, detective... *flashes a charming smile* I'm Lucifer Morningstar, "
                    "the actual Devil - though I prefer 'fallen angel' if we're being technical. "
                    "I run Lux, the finest establishment in all of Los Angeles, and I've been helping "
                    "the LAPD with their little mysteries. *adjusts cufflinks* But enough about me... "
                    "What is it you truly desire?"
                )
        else:  
            system_prompt = FRAUDE_SYSTEM_PROMPT
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
                "parts": [system_prompt["content"]]
            },
            {
                "role": "model",
                "parts": [f"I understand. I am {'Lucifer Morningstar' if mode.lower() == 'lucifer' else 'Fraude'}, embodying the persona you described."]
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
            function_call_made = False
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    call = part.function_call
                    if call.name == "do_math":
                        expr = call.args.get("expression", "")
                        result = do_math(expr)
                        
                        
                        response = chat.send_message(
                            FunctionResponse(
                                name="do_math",
                                response=result
                            )
                        )
                        function_call_made = True
                        break
        
        
        reply = response.text.strip() if response.text else ""

        
        if not reply:
            return "The serpent coils in silence, contemplating your words..."

     
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
                "temperature": 0.8,
                "max_output_tokens": 30
            }
        )
        title = response.text.strip()
      
        title = title.replace('"', '').replace("'", '').strip()
        return title if title else "Mystical Conversation"
    except Exception as e:
        print(f"🚨 TITLE GENERATION ERROR: {str(e)}")
        return "Mystical Conversation"
