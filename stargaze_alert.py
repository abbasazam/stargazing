import os
import requests
from datetime import datetime
import pytz
from google import genai
import smtplib
from email.mime.text import MIMEText

# Middle Fork River Forest Preserve Coordinates (Penfield, IL - Dark Sky Park)
LAT = 40.2831
LON = -87.9714

# --- NOTIFICATION CONFIGURATION ---
SENDER_EMAIL = "abbasazam004@gmail.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# List of recipient email addresses
RECIPIENT_EMAILS = [
    "abbasazam004@gmail.com",
    "abbasazam002@gmail.com",
    "kazam8513@stu.d214.org",
    "khadijaazam400@gmail.com",
    "chaudhrynabila4@gmail.com",
    "khadijaschool234@gmail.com",
]

# Set to True to get a status update even when conditions fail deep-sky standards.
# Set to False to ONLY receive emails when naked-eye deep-sky conditions are PERFECT.
SEND_IF_CONDITIONS_POOR = True


def fetch_72h_astronomy_forecast():
    """Fetches key stargazing weather and lunar metrics for the next 72 hours via Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "cloudcover,cloudcover_low,cloudcover_mid,cloudcover_high,relative_humidity_2m,wind_speed_10m,visibility",
        "daily": "moonrise,moonset,moon_phase",
        "forecast_hours": 72,
        "timezone": "America/Chicago"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def evaluate_with_llm(forecast_json):
    """Passes raw forecast to Gemini to evaluate if conditions and target seasonality 
    permit clear naked-eye visibility of deep-sky targets."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    chicago_tz = pytz.timezone("America/Chicago")
    now = datetime.now(chicago_tz)
    now_str = now.strftime("%Y-%m-%d %I:%M %p %Z")
    current_month = now.strftime("%B")
    
    prompt = f"""
    You are an expert astronomer evaluating night sky viewing conditions at Middle Fork River Forest Preserve (Latitude ~40.3° N).
    CURRENT TIME RIGHT NOW: {now_str} (Current Month: {current_month})
    
    HOURLY WEATHER FORECAST (Next 72 Hours):
    {forecast_json['hourly']}

    DAILY LUNAR DATA (Moonrise, Moonset, Moon Phase):
    {forecast_json.get('daily', {})}

    SEASONAL OBJECT VISIBILITY RULES (Latitude 40.3° N):
    Evaluate object availability based on the CURRENT MONTH ({current_month}):
    1. Milky Way Core (Sagittarius/Scorpius region):
       - Visible ONLY late April through September (Prime window: June–August).
       - October to March: The Galactic Core is behind the Sun or below the horizon at night. DO NOT promise Milky Way Core visibility in autumn/winter.
    2. Andromeda Galaxy (M31):
       - Visible August through February (Prime zenith window: October–December).
       - May to July: Low on horizon or obscured until late morning twilight.
    3. Orion Nebula (M42):
       - Visible November through March (Prime window: December–February).
       - May to September: Inaccessible at night.

    STRICT VISIBILITY GOAL (NAKED-EYE HUMAN VISION):
    We are looking ONLY for exceptional deep-sky viewing windows where:
    1. The Milky Way galaxy structure and dust lanes are CLEARLY visible as a bright, silvery band to the naked eye (if seasonally above horizon).
    2. Major naked-eye deep-sky targets (Andromeda Galaxy M31 as a soft oval cloud, and Orion Nebula M42) are detectable to the naked eye or small binoculars.

    EVALUATION CRITERIA FOR "ALERT: YES":
    - Seasonality Check: At least ONE major target (Milky Way Core or Andromeda/Major Nebulae) MUST be seasonally well-positioned above the horizon during the dark window for {current_month}.
    - Cloud Cover: Total cloud cover MUST be extremely low (<10-15%), with zero low/mid cloud obstruction during dark hours (9 PM to 4 AM CDT).
    - Transparency & Haze: Low relative humidity (<75-80%) and high horizontal visibility (>15,000 meters / 15 km) to prevent atmospheric haze.
    - Moonlight Interference (CRITICAL):
      * The Moon MUST be either below the horizon (set) during the midnight hours OR near New Moon (<15% illumination).
      * IF a bright Moon (>25% illuminated) is above the horizon during the dark night hours, it will wash out the Milky Way core and faint nebulae. You MUST output "ALERT: NO" if this occurs.
    - Surface Wind: Low surface winds (<10 mph) for atmospheric stability.

    INSTRUCTIONS & OUTPUT FORMAT:
    1. Look STRICTLY at UPCOMING night hours starting AFTER {now_str}.
    2. Output "ALERT: YES" ONLY if both atmospheric conditions AND target seasonality align for naked-eye deep-sky visibility. Otherwise, output "ALERT: NO".
    
    Format your output strictly in two parts:
    Line 1 MUST be either "ALERT: YES" or "ALERT: NO".
    Line 2+ should be a clear summary covering:
       - Seasonal Availability: Which deep-sky targets are actually above the horizon tonight in {current_month}.
       - Best Viewing Window: Specific date and time range (e.g., "Saturday 10:30 PM – 2:00 AM").
       - Weather & Transparency Breakdown: Cloud percentages, humidity/haze status, wind.
       - Lunar Status: Moon phase % and whether the Moon has set during dark hours.
       - Target Visibility Verdict: Explicit status for Milky Way Core, Andromeda (M31), and nebulae.
    """
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text




def send_email_alerts(subject, body, recipients):
    """Sends email alerts to a list of recipient email addresses via Gmail SMTP."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        print(f"Emails successfully sent to: {', '.join(recipients)}")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    print("Fetching 72-hour weather and lunar data from Open-Meteo...")
    raw_forecast = fetch_72h_astronomy_forecast()
    
    print("Evaluating deep-sky & Milky Way visibility with AI...")
    analysis = evaluate_with_llm(raw_forecast)
    print("\n--- LLM Response ---")
    print(analysis)
    
    if "ALERT: YES" in analysis:
        print("\nPrime deep-sky conditions detected! Sending alert emails...")
        subject = "🌌 Deep-Sky Alert: Milky Way Core & Andromeda Visibility at Middle Fork!"
        send_email_alerts(subject, analysis, RECIPIENT_EMAILS)
        
    else:
        print("\nConditions do not meet deep-sky / Milky Way standards.")
        if SEND_IF_CONDITIONS_POOR:
            print("Sending 'Sub-Optimal Conditions' status email...")
            
            subject = "☁️ Stargazing Update: Milky Way / Deep Sky Not Recommended Over Next 72h"
            
            poor_body = (
                "NO ALERT: Conditions over the next 72 hours will NOT permit clear viewing of "
                "the Milky Way core, Andromeda Galaxy, or faint nebulae.\n\n"
                "--- AI Breakdown ---\n"
                f"{analysis}"
            )
            
            send_email_alerts(subject, poor_body, RECIPIENT_EMAILS)
