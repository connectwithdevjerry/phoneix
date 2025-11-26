import openai, os

openai.api_key = "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"

def generate_smart_recommendation(
    lon: float,
    lat: float,
    user_intent: str = "buy land for building a house",  # e.g., "farming", "solar farm", "factory", "school"
    user_name: str = "there",
    flood_susceptibility: str = "Moderate",
    vhi: float = 50.0,
    lst_temp: float = 30.0,
    lst_category: str = "Moderate",
    drought: str = "Moderate"
) -> str:
    """
    Uses GPT-4o to generate a natural, trustworthy recommendation
    based on flood risk + user goal.
    """

    prompt = f"""
You are a senior land development and flood risk expert in Nigeria.
A user named {user_name} is asking about a plot of land at coordinates ({lon:.5f}, {lat:.5f}).

Their intention: {user_intent}

Our scientific flood susceptibility model (based on elevation, rainfall, rivers, soil, land cover, and flow accumulation from 2018–2025 data) classifies this location as:

→ flood_susceptibility: **{flood_susceptibility}**
→ drought: **{drought}**
→ vegetation health index (VHI): **{vhi}**
→ land surface temperature (LST): **{lst_temp}°C** ({lst_category})

Write a short, clear, professional, and friendly message (max 280 characters for Telegram) in simple English that includes:

1. The risk level
2. One-sentence explanation why
3. Strong recommendation (Go ahead / Proceed with caution / Not recommended)
4. One practical next step or alternative suggestion

Tone: Warm, trustworthy, expert — like a senior engineer advising a client.

Examples:
- "Hi John, this area is Very High Risk due to proximity to River Niger. I strongly advise against building here — consider higher grounds in Oyo or Kaduna."
- "Good news! This location is Low Risk. Perfectly safe for your house. Just ensure proper drainage."
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o",  # or "gpt-4o-mini" for cheaper/faster
        messages=[
            {"role": "system", "content": "You are a helpful Nigerian land and flood risk advisor."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()