import os

from dotenv import load_dotenv
from google import genai

from agents.query_agent import detect_intent


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


def coordinate(message):

    text = message.lower().strip()

    # --------------------------------
    # 1. ORDER ROUTING
    # --------------------------------

    # Order number
    if "order" in text and any(char.isdigit() for char in text):
        return "order"

    # Order tracking
    if any(word in text for word in [
        "track",
        "tracking",
        "where is my order",
        "where is my package",
        "package location",
        "order status"
    ]):
        return "order"


    # --------------------------------
    # 2. CANCEL ROUTING
    # --------------------------------

    if any(word in text for word in [
        "cancel",
        "cancel order",
        "cancel my order",
        "want to cancel"
    ]):
        return "cancel"


    # --------------------------------
    # 3. ESCALATION ROUTING
    # --------------------------------

    if any(word in text for word in [
        "damaged",
        "broken",
        "defective",
        "wrong product",
        "wrong item",
        "received damaged",
        "product not working",
        "not working",
        "complaint",
        "complain",
        "speak to agent",
        "human agent",
        "talk to support",
        "urgent"
    ]):
        return "escalation"


    # --------------------------------
    # 4. FAQ ROUTING
    # --------------------------------

    # Refund
    if any(word in text for word in [
        "refund",
        "money back",
        "get my money",
        "return my money",
        "reimbursement",
        "money returned"
    ]):
        return "faq"


    # Payment
    if any(word in text for word in [
        "payment",
        "upi",
        "credit card",
        "debit card",
        "net banking"
    ]):
        return "faq"


    # Delivery
    if any(word in text for word in [
        "delivery time",
        "delivery",
        "shipping",
        "how long"
    ]):
        return "faq"


    # Return / Exchange
    if any(word in text for word in [
        "return policy",
        "return product",
        "exchange",
        "replace product"
    ]):
        return "faq"


    # General support
    if any(word in text for word in [
        "support",
        "help",
        "customer care"
    ]):
        return "faq"


    # --------------------------------
    # 5. QUERY AGENT
    # --------------------------------

    intent = detect_intent(message)

    if intent == "track_order":
        return "order"

    if intent == "refund":
        return "faq"

    if intent == "cancel_order":
        return "cancel"

    if intent == "escalate":
        return "escalation"


    # --------------------------------
    # 6. GEMINI ROUTING
    # --------------------------------

    prompt = f"""
You are the routing agent for SmartSupport AI.

Classify the customer message into exactly ONE category.

Categories:

order
faq
cancel
escalation

Rules:

- order = order tracking, order status, package location
- faq = refund, payment, delivery, return policy, general information
- cancel = cancelling an order
- escalation = damaged product, broken product, serious complaint,
  urgent issue, or request for a human support agent

Customer message:

{text}

Return ONLY the category name.
"""


    try:

        response = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )

        route = response.output_text.strip().lower()

        if route in [
            "order",
            "faq",
            "cancel",
            "escalation"
        ]:
            return route

    except Exception:
        pass


    # --------------------------------
    # 7. DEFAULT
    # --------------------------------

    return "faq"