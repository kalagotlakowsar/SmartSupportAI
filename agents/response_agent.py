import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


def generate_ai_response(user_message, context):

    # --------------------------------
    # FAST LOCAL RESPONSES
    # --------------------------------

    context_lower = context.lower()

    if "status" in context_lower:

        return f"""Hello! 👋

{context}

Please let me know if you need any other assistance."""

    if "refund" in context_lower:

        return f"""I understand you're looking for a refund.

{context}

If you need any additional help, I'm happy to assist you."""

    if "cancel" in context_lower:

        return f"""Sure! 

{context}"""

    if "payment" in context_lower:

        return f"""Here is the payment information:

{context}"""

    # --------------------------------
    # AI FALLBACK
    # --------------------------------

    prompt = f"""
You are SmartSupport AI, a helpful customer support assistant.

Customer message:
{user_message}

Verified information:
{context}

Instructions:
- Give a short and friendly response.
- Be professional.
- Use ONLY the verified information.
- Do not invent order details, policies, prices, or information.
- Clearly answer the customer's question.
- If the information is insufficient, say so politely.
"""

    try:

        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )

        return interaction.output_text.strip().replace("\n\n", "\n")

    except Exception:

        return context