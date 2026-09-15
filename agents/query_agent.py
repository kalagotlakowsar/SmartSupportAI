import re


def detect_intent(message):

    message = message.lower().strip()

    # --------------------------------
    # CANCEL ORDER
    # --------------------------------

    cancel_words = [
        "cancel",
        "cancel order",
        "don't need this order",
        "do not need this order",
        "stop my order",
        "remove my order"
    ]

    for word in cancel_words:
        if word in message:
            return "cancel_order"


    # --------------------------------
    # REFUND
    # --------------------------------

    refund_words = [
        "refund",
        "money back",
        "get my money",
        "want my money",
        "return my money",
        "reimbursement",
        "money returned"
    ]

    for word in refund_words:
        if word in message:
            return "refund"


    # --------------------------------
    # ESCALATION
    # --------------------------------

    escalation_words = [
        "damaged",
        "broken",
        "defective",
        "not working",
        "wrong product",
        "wrong item",
        "complaint",
        "urgent",
        "speak to agent",
        "human agent",
        "customer care",
        "product issue"
    ]

    for word in escalation_words:
        if word in message:
            return "escalate"


    # --------------------------------
    # ORDER TRACKING
    # --------------------------------

    order_words = [
        "order",
        "track",
        "tracking",
        "package",
        "shipment",
        "where is my package",
        "where is my order",
        "where is my shipment",
        "delivery status"
    ]

    for word in order_words:
        if word in message:
            return "track_order"


    # --------------------------------
    # GENERAL
    # --------------------------------

    return "general"


def extract_order_id(message):

    match = re.search(r'\b\d{1,10}\b', message)

    if match:
        return match.group()

    return None