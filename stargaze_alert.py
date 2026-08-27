import os
import requests
from google import genai

# Middle Fork River Forest Preserve Coordinates (Penfield, IL)
LAT = 40.2831
LON = -87.9714

def fetch_48h_astronomy_forecast():
    """Fetches key stargazing weather metrics for the next 48 hours via Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "cloudcover,cloudcover_low,cloudcover_mid,cloudcover_high,relativehumidity_2m,windspeed_10m,visibility",
        "forecast_days": 2,
        "timezone": "America/Chicago"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def evaluate_with_llm(forecast_json):
    """Passes the raw 48-hour forecast to an LLM to evaluate stargazing conditions."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
    You are an expert astronomer assistant evaluating night sky viewing conditions.
    Below is the raw 48-hour hourly weather forecast for Middle Fork River Forest Preserve (Dark Sky Park).
    
    FORECAST DATA:
    {forecast_json['hourly']}

    INSTRUCTIONS:
    1. Look specifically at the night hours (roughly 9 PM to 4 AM CDT) over the next 48 hours.
    2. Focus on low cloud cover (<20%), low relative humidity (good transparency), and low wind speed (<10 mph).
    3. Determine if there is a prime viewing window coming up within the next 48 hours.
    4. Format your output strictly in two parts:
       Line 1 MUST be either "ALERT: YES" or "ALERT: NO".
       Line 2+ should be a clear, non-technical summary (2-3 sentences) explaining why, including the best time window.
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def send_alert_email(subject, body):
    """Sends an email alert using Python's built-in smtplib."""
    import smtplib
    from email.mime.text import MIMEText

    # Configuration 
    SENDER_EMAIL = "abbasazam004@gmail.com"  # Replace with your Gmail address
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
    RECIPIENT_EMAIL = "abbasazam004@gmail.com"  # Replace with where you want alerts sent

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())

if __name__ == "__main__":
    print("Fetching weather data from Open-Meteo...")
    raw_forecast = fetch_48h_astronomy_forecast()
    
    print("Evaluating stargazing quality with AI...")
    analysis = evaluate_with_llm(raw_forecast)
    print("\n--- LLM Response ---")
    print(analysis)
    
    if "ALERT: YES" in analysis:
        print("\nGood conditions detected! Sending alert...")
        send_alert_email("✨ Stargazing Alert: Middle Fork Preserve!", analysis)
    else:
        print("\nConditions are sub-optimal. No alert sent.")
