import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Testing Gemini API...")
print(f"API Key (first 15 chars): {api_key[:15]}...")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

print("\nSending test request...")
response = model.generate_content("Calculate 15 + 27. Respond with just the number.")
print(f"Response: {response.text}")
print("\n✅ Gemini API working!")