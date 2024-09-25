import os
import requests
import datetime
from twilio.rest import Client
STOCK = "MSFT"
COMPANY_NAME = "Microsoft Corp"
phone_number = "ENTER YOUR PHONE NUMBER HERE"


# Get news from newsAPI and send an SMS to the phone number with twilio
stock_params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "outputsize": "COMPACT",
    "datatype": "json",
    "apikey": os.environ.get("ALPHAVANTAGE_API_KEY")
}
stock_response = requests.get("https://www.alphavantage.co/query", stock_params)
stock_response.raise_for_status()
# print(stock_response.json())
today = datetime.date.today()
# Variable for tracking stock price change used later
price_change = 0
# Get dates, yesterday and day before yesterday because of limitations of free version of alphavantage
day_before_yesterday = today-datetime.timedelta(days=2)
yesterday = today-datetime.timedelta(days=1)
# Try catch in case Stock API reaches request limit
try:
    # Get value for day before yesterday
    day_before_yesterday_value = 0
    # If day before yesterday is sunday set it to last friday instead
    if day_before_yesterday.weekday() == 6:
        day_before_yesterday = today-datetime.timedelta(days=4)
    if day_before_yesterday.weekday() < 5:
        date = day_before_yesterday.strftime("%Y-%m-%d")
        day_before_yesterday_value = float(stock_response.json()["Time Series (Daily)"][date]["4. close"])
    # Get value for yesterday
    yesterday_value = 0
    if yesterday.weekday() < 5:
        date = yesterday.strftime("%Y-%m-%d")
        yesterday_value = float(stock_response.json()["Time Series (Daily)"][date]["4. close"])
    # If yesterday or day before is a weekend then set the value to the other day
    if day_before_yesterday_value == 0:
        day_before_yesterday_value = yesterday_value
    elif yesterday_value == 0:
        yesterday_value = day_before_yesterday_value
    # Check if the change in the stock price is greater than 5%
    price_change = abs(day_before_yesterday_value-yesterday_value)/yesterday_value*100
except KeyError:
    print(stock_response.json()["Information"])


if price_change >= 3:
    # Get news from newsAPI
    news_params = {
        "apiKey": os.environ.get("NEWS_API_KEY"),
        "qInTitle": COMPANY_NAME,
        "from": day_before_yesterday,
        "to": yesterday,
        "language": "en",
        "sortBy": "popularity"
    }
    news_response = requests.get("https://newsapi.org/v2/everything?", news_params)
    news_response.raise_for_status()
    # Get the most popular article
    article = news_response.json()["articles"][0]
    headline = article["title"]
    brief = article["content"]
    url = article["url"]
    # Use twilio to send an SMS
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)
    change_message = ""
    if price_change > 0:
        change_message = f"🔺{round(price_change, 2)}%"
    elif price_change < 0:
        change_message = f"🔻{round(price_change, 2)}%"
    message = client.messages.create(
        from_=os.environ.get("TWILIO_PHONE_NUMBER"),
        to=phone_number,
        body=f"{STOCK}: {change_message}\nHeadline: {headline}\nBrief:{brief}\nArticle: {url}"
    )
    print(message.sid)
