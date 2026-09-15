def analyze_sentiment(message):
    
    message = message.lower().strip()

    # --------------------------------
    # NEGATIVE SENTIMENT
    # --------------------------------

    negative_words = [
        "angry",
        "frustrated",
        "terrible",
        "worst",
        "bad",
        "complaint",
        "disappointed",
        "useless",
        "not working",
        "broken",
        "unhappy",
        "annoyed",
        "poor",
        "horrible",
        "disgusted",
        "upset",
        "problem",
        "issue"
    ]

    # --------------------------------
    # POSITIVE SENTIMENT
    # --------------------------------

    positive_words = [
        "happy",
        "good",
        "great",
        "excellent",
        "thank you",
        "thanks",
        "awesome",
        "amazing",
        "perfect",
        "satisfied",
        "helpful",
        "love"
    ]

    # Check negative words first
    for word in negative_words:

        if word in message:
            return "negative"

    # Check positive words
    for word in positive_words:

        if word in message:
            return "positive"

    # No strong emotion detected
    return "neutral"