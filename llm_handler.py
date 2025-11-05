import os
import google.generativeai as genai
import json
import re
from typing import Optional
import base64

class LLMHandler:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.0 Flash for speed and cost efficiency
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,
            }
        )
        
        print("✓ LLM Handler initialized with Gemini 2.0 Flash")
    
    async def query(self, prompt: str, response_format: str = "text", max_tokens: int = 4000):
        """Query Gemini with a prompt"""
        
        try:
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini")
            
            result = response.text
            
            if response_format == "json":
                # Extract JSON from markdown code blocks if present
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0].strip()
                
                # Try to parse to validate
                try:
                    json.loads(result)
                except:
                    # If parsing fails, try to extract JSON pattern
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        result = json_match.group(0)
            
            return result
            
        except Exception as e:
            raise Exception(f"Gemini API query failed: {e}")
    
    async def analyze_with_vision(self, image_data: bytes, prompt: str):
        """Analyze an image with vision capabilities"""
        try:
            from PIL import Image
            from io import BytesIO
            
            image = Image.open(BytesIO(image_data))
            
            response = self.model.generate_content([prompt, image])
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Vision analysis failed: {e}")