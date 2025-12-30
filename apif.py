import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file for local development
load_dotenv()

# Read API key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found. Add it to your .env file.")

# Configure Google GenAI
genai.configure(api_key=API_KEY)


def generate_mcq(topic: str, num_questions: int = 1) -> str:
    """
    Generates MCQs using Gemini model in a strict, parser-friendly format.
    """

    prompt = f"""
You are an exam question generator.

Generate exactly {num_questions} JEE/competitive-exam style MCQs on the topic: "{topic}".

STRICT FORMAT FOR EACH QUESTION:

1) First line:
<number>. <question text>

2) Then exactly four options, one per line:
A) <option A>
B) <option B>
C) <option C>
D) <option D>

3) Then the correct option on its own line:
Answer: <one letter from A, B, C, or D>

4) Then a brief explanation on its own line:
Explanation: <short explanation in 1–3 sentences>

VERY IMPORTANT CONTENT RULES:
- Options must only contain the option text (numbers, values, formulas, or short phrases).
- Do NOT put any reasoning, derivation, comments, or "This is simple", "Wait", etc. inside the options.
- All reasoning must go ONLY in the Explanation line.
- Do NOT talk about correcting yourself (no text like "I marked C by mistake", "Let me fix", "options don't match", etc.).
- Make sure the Explanation is already consistent with the options and the Answer.
- Do NOT write any extra lines before question 1 or after the last Explanation.
- Do NOT write things like "Here are some questions" or "MCQs below".

Math:
- Use LaTeX math inside $...$ where needed (for example $v^2 = u^2 + 2as$).
- Keep everything in clear exam style.
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        # Return the error as plain text so it shows up in the UI
        return f"Error: {str(e)}"
