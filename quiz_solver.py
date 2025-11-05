import asyncio
import requests
from playwright.async_api import async_playwright
import json
from llm_handler import LLMHandler
from data_processor import DataProcessor
import os
import re

class QuizSolver:
    def __init__(self):
        self.llm = LLMHandler()
        self.processor = DataProcessor()
        self.email = os.getenv("STUDENT_EMAIL")
        self.secret = os.getenv("SECRET_STRING")
    
    async def solve_quiz_chain(self, start_url: str):
        """Solve a chain of quiz questions"""
        current_url = start_url
        question_count = 0
        max_questions = 20  # Safety limit
        
        print(f"\n{'='*70}")
        print(f"🚀 Starting quiz chain from: {start_url}")
        print(f"{'='*70}\n")
        
        while current_url and question_count < max_questions:
            question_count += 1
            print(f"\n{'─'*70}")
            print(f"📝 QUESTION {question_count}")
            print(f"{'─'*70}")
            print(f"URL: {current_url}\n")
            
            try:
                # Fetch and parse the quiz page
                question_text = await self.fetch_quiz_page(current_url)
                print(f"\n✓ Question fetched ({len(question_text)} characters)")
                print(f"Preview:\n{question_text[:400]}...\n")
                
                # Solve the question using LLM
                answer, submit_url = await self.solve_question(question_text)
                print(f"\n💡 Answer calculated: {answer}")
                print(f"📤 Submitting to: {submit_url}\n")
                
                # Submit the answer
                response = self.submit_answer(submit_url, answer)
                print(f"Response received:")
                print(json.dumps(response, indent=2))
                
                # Check if correct and get next URL
                if response.get('correct'):
                    print("\n✅ CORRECT!")
                else:
                    print("\n❌ INCORRECT")
                
                current_url = response.get('url')
                
                if current_url:
                    print(f"\n➡️  Next question URL received")
                else:
                    print(f"\n🏁 No more questions - Quiz complete!")
                
                # Small delay between questions
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"\n❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print(f"\n{'='*70}")
        print(f"📊 QUIZ SUMMARY")
        print(f"{'='*70}")
        print(f"Total questions attempted: {question_count}")
        print(f"{'='*70}\n")
        
        return {"questions_solved": question_count}
    
    async def fetch_quiz_page(self, url: str) -> str:
        """Fetch and render JavaScript-based quiz page"""
        print("  [1/3] Launching browser...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print("  [2/3] Loading page...")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for JS execution
                
                print("  [3/3] Extracting content...")
                
                # Try to get the decoded content from #result element
                try:
                    result_element = await page.query_selector('#result')
                    if result_element:
                        content = await result_element.inner_text()
                        print("      → Extracted from #result element")
                    else:
                        content = await page.content()
                        print("      → Using full page content")
                except:
                    content = await page.content()
                    print("      → Using full page content (fallback)")
                
                await browser.close()
                return content
                
            except Exception as e:
                await browser.close()
                raise Exception(f"Failed to fetch quiz page: {e}")
    
    async def solve_question(self, question_text: str):
        """Use LLM to understand and solve the question"""
        
        print("\n  [STEP 1] Parsing question with LLM...")
        
        # Parse the question using LLM
        parse_prompt = f"""Analyze this quiz question and extract key information.

QUESTION TEXT:
{question_text}

Extract and return a JSON object with these fields:
1. "data_url": URL where data needs to be downloaded (or null if no download)
2. "task": Clear description of the calculation/analysis needed
3. "submit_url": URL where the answer should be POSTed
4. "answer_format": "number", "string", "boolean", or "object"

Return ONLY valid JSON, no other text.

Example:
{{
    "data_url": "https://example.com/data.pdf",
    "task": "Calculate the sum of the 'amount' column on page 2",
    "submit_url": "https://example.com/submit",
    "answer_format": "number"
}}

JSON:"""
        
        try:
            parsed = await self.llm.query(parse_prompt, response_format="json")
            parsed_data = json.loads(parsed)
            print(f"      ✓ Parsed successfully")
            print(f"      → Task: {parsed_data.get('task', 'N/A')[:80]}...")
            print(f"      → Data URL: {parsed_data.get('data_url', 'None')}")
            print(f"      → Submit URL: {parsed_data.get('submit_url', 'N/A')}")
        except Exception as e:
            print(f"      ✗ LLM parsing failed: {e}")
            print(f"      → Attempting manual parsing...")
            parsed_data = self._manual_parse(question_text)
        
        # Download data if needed
        data = None
        if parsed_data.get('data_url'):
            print(f"\n  [STEP 2] Downloading data...")
            try:
                data = await self.processor.download_data(parsed_data['data_url'])
                print(f"      ✓ Data downloaded")
            except Exception as e:
                print(f"      ✗ Download failed: {e}")
        else:
            print(f"\n  [STEP 2] No data download needed")
        
        # Solve the actual question
        print(f"\n  [STEP 3] Analyzing and calculating answer...")
        
        if data is not None:
            answer = await self.processor.process_and_analyze(data, parsed_data.get('task', question_text))
        else:
            # No data file, answer from question text directly
            solve_prompt = f"""Answer this question directly.

QUESTION: {parsed_data.get('task', question_text)}

CONTEXT:
{question_text[:500]}

Provide ONLY the answer. Format: {parsed_data.get('answer_format', 'string')}
No explanation, just the answer.

ANSWER:"""
            
            answer = await self.llm.query(solve_prompt)
            answer = self.processor._extract_answer(answer)
        
        print(f"      ✓ Answer calculated: {answer}")
        
        # Convert answer to appropriate type
        answer = self._format_answer(answer, parsed_data.get('answer_format', 'string'))
        
        return answer, parsed_data.get('submit_url', '')
    
    def _manual_parse(self, question_text: str):
        """Fallback manual parsing if LLM fails"""
        # Try to find URLs using regex
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, question_text)
        
        data_url = None
        submit_url = None
        
        for url in urls:
            if 'submit' in url.lower() or 'answer' in url.lower():
                submit_url = url
            elif any(ext in url.lower() for ext in ['.pdf', '.csv', '.json', '.xlsx', '.xls']):
                data_url = url
        
        # If no submit URL found, use the first URL
        if not submit_url and urls:
            submit_url = urls[-1]  # Use last URL as submit URL
        
        return {
            "data_url": data_url,
            "task": "Analyze the data and provide the answer as requested in the question",
            "submit_url": submit_url or "",
            "answer_format": "string"
        }
    
    def _format_answer(self, answer, format_type):
        """Format answer based on expected type"""
        if format_type == "number":
            try:
                # Remove commas, spaces, and convert to number
                answer_str = str(answer).replace(',', '').replace(' ', '').strip()
                # Return int if no decimal, else float
                return float(answer_str) if '.' in answer_str else int(float(answer_str))
            except:
                return answer
        elif format_type == "boolean":
            return str(answer).lower() in ['true', '1', 'yes', 'correct', 'y']
        elif format_type == "object":
            if isinstance(answer, str):
                try:
                    return json.loads(answer)
                except:
                    return {"value": answer}
            return answer
        
        # Default: return as string
        return str(answer).strip()
    
    def submit_answer(self, submit_url: str, answer):
        """Submit answer to the specified endpoint"""
        payload = {
            "email": self.email,
            "secret": self.secret,
            "answer": answer
        }
        
        print(f"\n  [SUBMIT] Payload:")
        print(f"  {json.dumps(payload, indent=4)}")
        
        try:
            response = requests.post(submit_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"\n  ❌ HTTP Error {response.status_code}")
            print(f"  Response: {response.text}")
            return {"correct": False, "error": f"HTTP {response.status_code}", "details": response.text}
        except Exception as e:
            print(f"\n  ❌ Submission error: {e}")
            return {"correct": False, "error": str(e)}