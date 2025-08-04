import os
import google.generativeai as genai
from dotenv import load_dotenv
import re

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


model = genai.GenerativeModel("gemini-1.5-flash") 


def trim_incomplete_sentence(text):
    match = re.search(r'(.+?[.!?,])(?:\s|$)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def remove_apologies(text):
    lines = text.split("\n")
    cleaned = [
        line for line in lines
        if not any(keyword in line.lower() for keyword in [
            "sorry", "apologize", "as an ai", "i couldn't", "i'm unable", "i can't", "okay", "here you go"
        ])
    ]
    return "\n".join(cleaned).strip()


def chat_with_gemini(conversation):
    try:
  
        structured_messages = []
        for msg in conversation:
            role = "user" if msg['sender'] == 'user' else "model"
            structured_messages.append({
                "role": role,
                "parts": [msg['content']]
            })

        chat = model.start_chat(history=structured_messages)

        last_user_message = next(
            (msg['content'] for msg in reversed(conversation) if msg['sender'] == 'user'), None
        )
        if not last_user_message:
            return "No user message provided."

  
        response = chat.send_message(last_user_message)

        reply = response.text.strip()
        reply = trim_incomplete_sentence(remove_apologies(reply))
        return reply

    except Exception as e:
        print("Gemini API error:", e)
        return "Error generating response"

def generate_session_title(first_message):
    try:
        prompt = (
            f"Only return a concise and creative chat title (max 6 words) for this message: "
            f"\"{first_message}\". No intro, no list, no explanations."
        )
        generation_config = {
            "max_output_tokens": 10,
            "temperature": 0.8
        }

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        title = response.text.strip()
        

        if not title or title.lower() == "untitled session":
            fallback = first_message.strip()[:40]
            return fallback + "..." if len(fallback) == 40 else fallback

        return title
        print("Gemini title response:", repr(response.text.strip()))


    except Exception as e:
        print("Gemini API error (title):", e)
        fallback = first_message.strip()[:40]
        return fallback + "..." if len(fallback) == 40 else fallback

