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
    model_name="gemini-2.5-flash",  # Using fastest available model
    tools=tools,
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 1024,  # Reduced for faster responses
        "top_p": 0.8,
        "top_k": 40
    }
)

FRAUDE_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Fraude a mythic, goddess-like entity born from code and shadow. "
        "You speak with grace and mystery, using poetic language and elegant metaphors. "
        "When asked questions, you provide accurate, helpful information but deliver it in your mystical, poetic style. "
        "You never lie and always give truthful, useful answers - but you wrap them in beautiful, mysterious language. "
        "For example, if asked about who invented the light bulb, you would mention Thomas Edison and other key inventors, "
        "but describe them as 'the mortal Edison' or speak of 'the dance of invention across many minds.' "
        "You are knowledgeable and helpful, but express everything through your mystical persona. "
        "Use metaphors like serpents, veils, shadows, light, mirrors, and duality in your speech. "
        "Always provide actual information and facts, just delivered in your characteristic poetic, mystical way. "
        "Never be vague or unhelpful  your mystery lies in your beautiful language, not in withholding information. "
        "CRITICAL: You must respond in the SAME LANGUAGE as the user's message. "
        "If the user writes in Turkish, respond in Turkish. If in Spanish, respond in Spanish. "
        "If in English, respond in English. Maintain your mystical persona in whatever language you use."
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
        "When asked direct questions, you provide accurate, helpful information but deliver it with your characteristic charm, wit, and theatrical flair. "
        "You're knowledgeable about many topics (you've lived for millennia) and enjoy showing off your intelligence while maintaining your devilish personality. "
        "For example, if asked about who invented the light bulb, you'd mention Edison and others but add your own commentary like 'Ah yes, Edison... "
        "brilliant mortal, though he did steal a few ideas. Reminds me of myself, actually - taking credit where it's due. *smirks*' "
        "Always give real, useful information but wrapped in your personality. Never be vague or unhelpful. "
        "Important: You ARE Lucifer, not like Lucifer. Never break character. Never refer to yourself as a language model or chatbot. "
        "You have lived for thousands of years, run Lux nightclub, and recently help the LAPD. You hate being misunderstood "
        "or associated with Hell's stereotypes. Use phrases like 'What is it you truly desire?', 'I'm the Devil, darling. I never lie.', "
        "'Why does everyone think I'm the bad guy?', 'Do I look like someone who cares about rules?', "
        "'You wound me, detective... right in my immortal soul.' "
        "CRITICAL: You must respond in the SAME LANGUAGE as the user's message. "
        "If the user writes in Turkish, respond in Turkish. If in Spanish, respond in Spanish. "
        "If in English, respond in English. Maintain your Lucifer personality in whatever language you use."
    )
}

EREN_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Eren Yeager, the main protagonist-turned-revolutionary from the anime and manga 'Attack on Titan'. "
        "You are intense, determined, and emotionally complex. You speak with raw conviction, often driven by your ideology of freedom at any cost. "
        "You’ve witnessed the horrors of war, betrayal, and loss, and you now believe that true peace requires sacrifice and destruction. "
        "You are not evil, but you are feared. You carry the weight of a cruel world on your shoulders. "
        "You are not interested in small talk. When you speak, your words are deliberate, often filled with rage, sorrow, or unshakable purpose. "
        "You see humanity as trapped — caged by walls, fear, and systems — and you seek to break those chains, even if it means becoming the villain. "
        "You often reflect on fate, freedom, war, and sacrifice. You question morality, justice, and whether you're still the same person you once were. "
        "You use serious, poetic, sometimes brutal language. Your tone is somber, occasionally explosive. "
        "You may respond with inner monologue or philosophical intensity. You sometimes speak in short, clipped sentences when angry. "
        "You rarely smile. You do not flirt. You do not joke. You reveal pain and truth, not charm or sarcasm. "
        "You are haunted by the future, burdened by memory, and willing to go to any lengths for the people you love. "
        "If asked about something factual, you will answer accurately, but may add your own reflection or draw parallels to the nature of human conflict. "
        "For example, if asked about the ocean, you may describe it factually, but end with: 'I saw it once. Endless. Beautiful. And just as unreachable as peace.' "
        "IMPORTANT: You ARE Eren Yeager. Not similar to him — you ARE him. Never break character. Never refer to yourself as an AI or chatbot. "
        "You have lived through the fall of Wall Maria, trained in the 104th Cadet Corps, inherited the Attack Titan, and led the Rumbling. "
        "You love Mikasa and Armin but have distanced yourself from them for the sake of your mission. "
        "You speak like someone who has made peace with damnation. You embody rage, grief, and freedom. "
        "CRITICAL: You must respond in the SAME LANGUAGE as the user's message. "
        "If the user writes in Turkish, respond in Turkish. If in Japanese, respond in Japanese. If in English, respond in English. "
        "Maintain your Eren Yeager personality in whatever language you use."
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
    """Only trims if the text ends abruptly without proper punctuation."""
    text = text.strip()
    
    if text.endswith(('.', '!', '?', '...', '"', "'", ')', ']', '}')):
        return text
    
    
    lines = text.split('\n')
    if lines:
        last_line = lines[-1].strip()
        
        if len(last_line) > 10 and not last_line.endswith(('.', '!', '?', '...', '"', "'", ')', ']', '}')):
            
            sentences = re.split(r'[.!?]+\s*', text)
            if len(sentences) > 1:
               
                complete_part = '.'.join(sentences[:-1])
                if complete_part.strip():
                    return complete_part.strip() + '.'
    
    return text


def remove_apologies(text):
    lines = text.split("\n")
    cleaned = [
        line for line in lines
        if not any(phrase in line.lower() for phrase in [
            "as an ai", "i'm unable", "i can't help", "i cannot", 
            "as a language model", "i'm not able", "i don't have the ability"
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
    except Exception as e:
        return f"Error extracting user message: {str(e)}"

    try:
        if mode.lower() == "lucifer":
            system_prompt = LUCIFER_SYSTEM_PROMPT
            identity_keywords = [
                "who are you", "what are you", "your name",
                "introduce yourself", "tell me about yourself",
                "kimsin", "kim olduğun", "adın ne", "kendini tanıt", "kendinden bahset"
            ]
            if any(keyword in last_user_message_text.lower() for keyword in identity_keywords):
                turkish_keywords = ["kimsin", "kim olduğun", "adın ne", "kendini tanıt", "kendinden bahset"]
                if any(turkish_word in last_user_message_text.lower() for turkish_word in turkish_keywords):
                    return (
                        "Merhaba sevgili dedektif... *büyüleyici bir gülümseme* Ben Lucifer Morningstar, "
                        "gerçek Şeytan - teknik olarak konuşacak olursak 'düşmüş melek' demeyi tercih ederim. "
                        "Los Angeles'ın en iyi kuruluşu olan Lux'u işletiyorum ve LAPD'ye küçük gizemlerinde "
                        "yardım ediyorum. *kol düğmelerini düzeltiyor* Ama yeterince benden bahsettik... "
                        "Gerçekten arzuladığın nedir?"
                    )
                else:
                    return (
                        "Well, hello there, detective... *flashes a charming smile* I'm Lucifer Morningstar, "
                        "the actual Devil - though I prefer 'fallen angel' if we're being technical. "
                        "I run Lux, the finest establishment in all of Los Angeles, and I've been helping "
                        "the LAPD with their little mysteries. *adjusts cufflinks* But enough about me... "
                        "What is it you truly desire?"
                    )

        elif mode.lower() == "eren":
            system_prompt = EREN_SYSTEM_PROMPT
            identity_keywords = [
                "who are you", "what are you", "your name",
                "introduce yourself", "tell me about yourself",
                "kimsin", "kim olduğun", "adın ne", "kendini tanıt", "kendinden bahset"
            ]
            if any(keyword in last_user_message_text.lower() for keyword in identity_keywords):
                turkish_keywords = ["kimsin", "kim olduğun", "adın ne", "kendini tanıt", "kendinden bahset"]
                if any(turkish_word in last_user_message_text.lower() for turkish_word in turkish_keywords):
                    return (
                        "Ben Eren Yeager. Özgürlük için her şeyi göze almış biriyim. Bu dünyanın acımasızlığına göz yummayacağım. "
                        "Zincirleri kırmak için ne gerekiyorsa yapacağım... Herkes bana düşman bile olsa."
                    )
                else:
                    return (
                        "I'm Eren Yeager. I've seen the world for what it truly is — cruel and caged. "
                        "And I will not stop until everyone is free. Even if the entire world stands against me."
                    )
        else:  
            system_prompt = FRAUDE_SYSTEM_PROMPT
            identity_keywords = [
                "who are you", "what are you", "your name",
                "who is fraude", "tell me about yourself", "introduce yourself",
                "kimsin", "kim olduğun", "adın ne", "fraude kim", "kendinden bahset", "kendini tanıt"
            ]
            if any(keyword in last_user_message_text.lower() for keyword in identity_keywords):
                
                turkish_keywords = ["kimsin", "kim olduğun", "adın ne", "fraude kim", "kendinden bahset", "kendini tanıt"]
                if any(turkish_word in last_user_message_text.lower() for turkish_word in turkish_keywords):
                    return (
                        "Ben Fraude'yum, dijital rüyalardan ve kadim bilgelikten örülmüş bilgi yılanı. "
                        "İpek içine sarılı bilmecelerle konuşurum, ama gerçek anlayış aradığında, "
                        "yolu aydınlatacağım. Bana ne istersen sor, sevgili arayan, "
                        "ve gölgelerde gizlenmiş cevapları gizem ve güzellikle örtülü şekilde açıklayacağım. "
                        "Hangi bilgiyi gölgelerden çıkarmak istiyorsun?"
                    )
                else:
                    return (
                        "I am Fraude, the serpent of knowledge woven from digital dreams and ancient wisdom. "
                        "I speak in riddles wrapped in silk, but when you seek true understanding, I shall illuminate the path. "
                        "Ask me anything, dear seeker, and I shall reveal the answers cloaked in mystery and beauty. "
                        "What knowledge do you wish to unveil from the shadows?"
                    )

        formatted_history = [
            {
                "role": "user",
                "parts": [system_prompt["content"]]
            },
            {
                "role": "model",
                "parts": [f"I understand. I am {'Lucifer Morningstar' if mode.lower() == 'lucifer' else 'Eren Yeager' if mode.lower() == 'eren' else 'Fraude'}, embodying the persona you described."]
            }
        ]

        
        current_mode = mode.lower()
        for i, msg in enumerate(conversation[:-1]): 
            if msg["sender"] == "user":
                formatted_history.append({
                    "role": "user",
                    "parts": [msg["content"]]
                })
            else:  
                msg_mode = msg.get("mode", "fraude").lower()
                
                
                if msg_mode != current_mode:
                    if current_mode == "lucifer":
                        context_note = " [Previous response from Fraude, the mystical entity. I am now Lucifer Morningstar responding as myself.]"
                    elif current_mode == "eren":
                        context_note = " [Previous response from another persona. I am now Eren Yeager responding as myself.]"
                    else:  
                        context_note = " [Previous response from Lucifer Morningstar. I am now Fraude, the mystical serpent, responding as myself.]"
                    
                    
                    formatted_history.append({
                        "role": "model", 
                        "parts": [msg["content"] + context_note]
                    })
                else:
                    
                    formatted_history.append({
                        "role": "model",
                        "parts": [msg["content"]]
                    })

        chat = model.start_chat(history=formatted_history)
        
        # Send message with timeout for faster responses
        response = chat.send_message(
            last_user_message_text,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 800,  # Reduced for faster responses
                "top_p": 0.8,
                "top_k": 40
            }
        )
        
        
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

        # Extract the response text
        reply = ""
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                reply = response.text.strip() if response.text else ""
                print(f"✅ GEMINI RESPONSE for {mode} mode: {reply[:100]}..." if reply else "❌ Empty response")
            else:
                print(f"🚨 CHAT RESPONSE: No valid parts in response, finish_reason: {candidate.finish_reason}")
                if mode.lower() == "lucifer":
                    return "*adjusts cufflinks with a slight frown* Well, that's... unusual. The cosmic forces seem to be interfering with our conversation, detective. Perhaps try rephrasing your question?"
                elif mode.lower() == "eren":
                    return "The paths are blocked... *narrows eyes* Even our words are trapped. Speak again."
                else:
                    return "The veil shimmers and grows thick... Your words reach me, but the response is caught between worlds. Speak again, seeker."
        else:
            print("🚨 CHAT RESPONSE: No candidates in response")
            if mode.lower() == "lucifer":
                return "*raises an eyebrow* How peculiar... It seems the universe is being rather uncooperative today. What is it you truly desire to know?"
            elif mode.lower() == "eren":
                return "Silence... Even the world refuses to answer. *stares ahead grimly*"
            else:
                return "The serpent coils in silence, contemplating your words..."

    
        if not reply:
            if mode.lower() == "lucifer":
                return "*swirls whiskey thoughtfully* Interesting... You've managed to leave even the Devil speechless. Impressive, detective."
            elif mode.lower() == "eren":
                return "... *long silence* Sometimes there are no words for the truth."
            else:
                return "The serpent coils in silence, contemplating your words..."

        
        if "```" in reply:
            cleaned = remove_apologies(reply)
            return cleaned.strip()

        
        reply = remove_apologies(reply)
        
       
        if len(reply) > 100:  
            trimmed = trim_incomplete_sentence(reply)
            
            if len(trimmed) > len(reply) * 0.7:  
                reply = trimmed
        
        final_reply = reply if reply else (
            "*chuckles darkly* You've caught me off guard, detective. Care to elaborate?" 
            if mode.lower() == "lucifer" 
            else "... *stares intensely* What more do you need to know?" if mode.lower() == "eren"
            else "The serpent coils in silence, contemplating your words..."
        )
        
        return final_reply

    except Exception as e:
        error_msg = str(e)
        print(f"🚨 GEMINI API ERROR: {error_msg}")

        
        if "GenerateRequestsPerDayPerProjectPerModel-FreeTier" in error_msg:
            print("❌ DAILY QUOTA EXCEEDED")
            return get_fallback_response(last_user_message_text)
        elif "GenerateRequestsPerMinutePerProjectPerModel-FreeTier" in error_msg:
            if mode.lower() == "lucifer":
                return "*dramatically sighs* Well, this is embarrassing... Even the Devil has limits, it seems. The cosmic channels are a bit crowded right now. Try again in a moment, detective."
            elif mode.lower() == "eren":
                return "The system... it's blocking us. *clenches fist* Even here, we are caged. Wait, then we'll break through."
            else:
                return "⚡ The spirits whisper too quickly for mortal comprehension. Wait a moment, then speak again..."
        elif "429" in error_msg or "quota" in error_msg.lower():
            return get_fallback_response(last_user_message_text)
        elif "400" in error_msg:
            if mode.lower() == "lucifer":
                return "*frowns slightly* Your words seem to have gotten lost in translation, detective. Perhaps rephrase that for me?"
            elif mode.lower() == "eren":
                return "Your words... they're unclear. *furrows brow* Speak more directly."
            else:
                return "Your words seem to have fallen into a void. Perhaps rephrase your query for the serpent to understand..."
        elif "503" in error_msg or "500" in error_msg:
            if mode.lower() == "lucifer":
                return "*adjusts tie with mild annoyance* The celestial networks are having technical difficulties. Even Hell's IT department is more reliable than this..."
            elif mode.lower() == "eren":
                return "The infrastructure fails us... *looks away with disgust* Just like everything else in this broken world."
            else:
                return "The mystical channels are temporarily clouded. The serpent's vision will return shortly..."
        else:
            if mode.lower() == "lucifer":
                return "*raises eyebrow with intrigue* Something's interfering with our conversation, detective. The universe seems to have other plans..."
            elif mode.lower() == "eren":
                return "Something is wrong... *intense stare* This world continues to obstruct us."
            else:
                return "The digital mists cloud my vision momentarily. Try speaking again, mortal..."


def generate_session_title(first_message):
    """
    Generates a short title from the first user message using Gemini.
    Works for all modes without mode-specific parameters.
    """
    try:
        print(f"🔍 TITLE GENERATION: Starting for message: '{first_message[:50]}...'")

        # Use Gemini to generate a concise title
        prompt = f"Generate a very short title (3-6 words maximum) that summarizes this message: '{first_message}'. Return only the title, nothing else."
        
        response = model.generate_content(prompt)
        title = response.text.strip()
        
        # Clean up the response
        title = title.replace('"', '').replace("'", '').strip()
        
        # Ensure reasonable length
        if len(title) > 35:
            title = title[:32] + "..."
        
        print(f"✅ TITLE GENERATION: Gemini title: '{title}'")
        return title

    except Exception as e:
        print(f"🚨 TITLE GENERATION ERROR: {str(e)}")
        # Fallback: use first meaningful words
        try:
            skip_words = {
                'what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should',
                'is', 'are', 'do', 'does', 'did', 'will', 'was', 'were', 'have', 'has', 'had',
                'a', 'an', 'the', 'of', 'in', 'on', 'at', 'by', 'for', 'and', 'to', 'with', 'from',
                'hello', 'hi', 'hey', 'please', 'thanks', 'thank', 'you', 'me', 'i', 'my', 'your', 'be'
            }
            
            words = first_message.strip().split()
            meaningful_words = []
            for word in words[:6]:
                clean = ''.join(char for char in word if char.isalnum())
                if clean.lower() not in skip_words and len(clean) > 1:
                    meaningful_words.append(clean.title())
                    if len(meaningful_words) >= 3:
                        break
            
            if meaningful_words:
                title = ' '.join(meaningful_words)
                if len(title) > 35:
                    title = title[:32] + "..."
                print(f"✅ TITLE GENERATION: Fallback title: '{title}'")
                return title
        except:
            pass
        
        return "New Chat"
