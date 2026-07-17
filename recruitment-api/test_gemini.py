from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("Gemini key loaded:", bool(api_key))
print("Key length:", len(api_key or ""))

try:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply only with the word OK"
    )

    print("Gemini response:")
    print(response.text)

except Exception as e:
    print("Gemini failed:")
    print(e)