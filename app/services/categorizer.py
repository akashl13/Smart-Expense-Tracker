KEYWORDS = {
    "Food": ("swiggy", "zomato", "restaurant", "cafe", "grocery", "food"),
    "Transportation": ("uber", "ola", "petrol", "fuel", "metro", "bus", "taxi"),
    "Entertainment": ("netflix", "spotify", "movie", "cinema", "prime", "concert"),
    "Shopping": ("amazon", "flipkart", "mall", "clothes", "shopping"),
    "Education": ("course", "book", "udemy", "school", "college"),
    "Healthcare": ("doctor", "hospital", "pharmacy", "medicine"),
    "Bills": ("electricity", "internet", "phone", "water", "bill"),
    "Rent": ("rent", "lease"),
    "Travel": ("hotel", "flight", "airbnb", "travel", "trip"),
}


def categorize(description, fallback="Other"):
    text = description.lower()
    for category, keywords in KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return fallback
