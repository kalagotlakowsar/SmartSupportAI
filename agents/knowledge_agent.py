faq = {

    "refund":
    "Refunds are processed within 5-7 business days.",

    "delivery":
    "Standard delivery takes 3-5 business days.",

    "cancel":
    "Orders can be cancelled before shipment.",

    "payment":
    "We accept UPI, Credit Card, Debit Card and Net Banking.",

    "return":
    "Products can be returned within 7 days of delivery.",

    "exchange":
    "Product exchange is available within 7 days.",

    "support":
    "Customer support is available 24/7.",

    "shipping":
    "Shipping is free for orders above ₹499."
}


def get_faq_response(message):

    message = message.lower().strip()

    # --------------------------------
    # REFUND
    # --------------------------------

    refund_words = [
        "refund",
        "money back",
        "get my money",
        "return my money",
        "reimbursement",
        "money returned",
        "want my money",
        "money back please"
    ]

    for word in refund_words:

        if word in message:
            return faq["refund"]


    # --------------------------------
    # DELIVERY
    # --------------------------------

    delivery_words = [
        "delivery",
        "deliver",
        "how long",
        "arrive",
        "when will it arrive",
        "delivery time"
    ]

    for word in delivery_words:

        if word in message:
            return faq["delivery"]


    # --------------------------------
    # PAYMENT
    # --------------------------------

    payment_words = [
        "payment",
        "pay",
        "upi",
        "credit card",
        "debit card",
        "net banking"
    ]

    for word in payment_words:

        if word in message:
            return faq["payment"]


    # --------------------------------
    # RETURN
    # --------------------------------

    return_words = [
        "return",
        "return product",
        "return item"
    ]

    for word in return_words:

        if word in message:
            return faq["return"]


    # --------------------------------
    # EXCHANGE
    # --------------------------------

    exchange_words = [
        "exchange",
        "replace",
        "replacement"
    ]

    for word in exchange_words:

        if word in message:
            return faq["exchange"]


    # --------------------------------
    # SUPPORT
    # --------------------------------

    support_words = [
        "support",
        "customer care",
        "customer support",
        "help"
    ]

    for word in support_words:

        if word in message:
            return faq["support"]


    # --------------------------------
    # SHIPPING
    # --------------------------------

    shipping_words = [
        "shipping",
        "shipping cost",
        "delivery charge",
        "delivery fee",
        "free shipping"
    ]

    for word in shipping_words:

        if word in message:
            return faq["shipping"]


    return None