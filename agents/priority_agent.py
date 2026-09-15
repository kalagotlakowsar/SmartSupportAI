def get_priority(sentiment):
    
    # Negative customer → High priority
    if sentiment == "negative":
        return "High"

    # Positive customer → Low priority
    elif sentiment == "positive":
        return "Low"

    # Neutral customer → Normal priority
    else:
        return "Normal"