FAMILY_SUPPORT_KEYWORDS = ["AMMI", "ABBA", "MOM", "DAD"]

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Eating Out": [
        "MCDONALD",
        "TIM HORTON",
        "STARBUCKS",
        "SUBWAY",
        "POPEYES",
        "WENDY",
        "BURGER KING",
        "KFC",
        "PIZZA",
        "CHIPOTLE",
        "PANDA EXPRESS",
        "FIVE GUYS",
        "SUSHI",
        "RESTAURANT",
        "CAFE",
        "DINER",
        "GRILL",
        "NANDO",
        "SWISS CHALET",
        "BOSTON PIZZA",
        "HARVEYS",
        "A&W",
        "MARY BROWN",
        "FRESHII",
        "PANERA",
        "SHAWARMA",
        "PHO",
        "RAMEN",
        "TACO",
        "WINGSTOP",
        "CHICK-FIL-A",
        "DOMINO",
        "PAPA JOHN",
    ],
    "Uber Eats": ["UBER EATS", "UBEREATS"],
    "Groceries": [
        "METRO",
        "LOBLAWS",
        "NO FRILLS",
        "FOOD BASICS",
        "FRESHCO",
        "SOBEYS",
        "WALMART",
        "COSTCO",
        "T&T",
        "FARM BOY",
        "REAL CANADIAN",
        "SUPERSTORE",
        "GROCERY",
        "ALDI",
        "WHOLE FOODS",
        "FORTINOS",
        "ZEHRS",
        "SHOPPERS",
    ],
    "Transportation - Rideshare": ["UBER TRIP", "UBER* TRIP", "LYFT"],
    "Transportation - Gas": ["PETRO", "SHELL", "ESSO", "PIONEER", "CANADIAN TIRE GAS", "ULTRAMAR"],
    "Transportation - Parking": ["PARKING", "IMPARK", "GREEN P", "HONK MOBILE"],
    "Transportation - Transit": ["PRESTO", "TTC", "GO TRANSIT", "METROLINX", "TRANSIT"],
    "Shopping": [
        "AMAZON",
        "APPLE.COM",
        "BEST BUY",
        "WINNERS",
        "MARSHALLS",
        "H&M",
        "ZARA",
        "UNIQLO",
        "GAP",
        "OLD NAVY",
        "NIKE",
        "ADIDAS",
        "DOLLARAMA",
        "CANADIAN TIRE",
        "HOME DEPOT",
        "IKEA",
    ],
    "Entertainment": [
        "NETFLIX",
        "DISNEY",
        "CRAVE",
        "CINEPLEX",
        "SPOTIFY",
        "APPLE MUSIC",
        "STEAM",
        "PLAYSTATION",
        "XBOX",
        "NINTENDO",
        "AMC",
    ],
    "Subscriptions": [
        "CHATGPT",
        "OPENAI",
        "ADOBE",
        "MICROSOFT 365",
        "GOOGLE STORAGE",
        "ICLOUD",
        "DROPBOX",
    ],
    "Health & Fitness": [
        "GYM",
        "GOODLIFE",
        "FIT4LESS",
        "LA FITNESS",
        "PLANET FITNESS",
        "PHARMACY",
        "REXALL",
    ],
    "Investment": ["QUESTRADE", "WEALTHSIMPLE", "INTERACTIVE BROKERS", "TD DIRECT"],
    "Internal Transfer": ["INTERNET TRANSFER", "TRANSFER OUT", "TRANSFER IN", "E-TRANSFER SENT"],
}

SKIP_PATTERNS = ["PAYMENT THANK YOU", "PAYMENT - THANK YOU", "THANK YOU"]


def categorize_transaction(description: str, family_recipients: list[str] | None = None) -> str:
    upper = description.upper()

    # Check for family support e-transfers first
    if family_recipients:
        for recipient in family_recipients:
            if recipient.upper() in upper:
                return "Family Support"

    # Check for skip patterns (these should still be categorized but might be filtered)
    for pattern in SKIP_PATTERNS:
        if pattern in upper:
            return "Credit Card Payment"

    # Uber disambiguation
    if "UBER" in upper:
        if "EATS" in upper:
            return "Uber Eats"
        return "Transportation - Rideshare"

    # Match against keyword categories
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in upper:
                return category

    return "Other"
