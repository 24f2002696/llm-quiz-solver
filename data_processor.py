import requests
import pandas as pd
import PyPDF2
import pdfplumber
from io import BytesIO
import json
import re
from llm_handler import LLMHandler

class DataProcessor:
    def __init__(self):
        self.llm = LLMHandler()
    
    async def download_data(self, url: str):
        """Download data from URL"""
        try:
            print(f"  → Downloading from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            if 'pdf' in content_type or url.lower().endswith('.pdf'):
                print("  → Detected PDF format")
                return self.extract_pdf_data(response.content)
            elif 'csv' in content_type or url.lower().endswith('.csv'):
                print("  → Detected CSV format")
                return pd.read_csv(BytesIO(response.content))
            elif 'json' in content_type or url.lower().endswith('.json'):
                print("  → Detected JSON format")
                return response.json()
            elif 'excel' in content_type or url.lower().endswith(('.xlsx', '.xls')):
                print("  → Detected Excel format")
                return pd.read_excel(BytesIO(response.content))
            else:
                print("  → Treating as text")
                return response.text
        except Exception as e:
            raise Exception(f"Failed to download data: {e}")
    
    def extract_pdf_data(self, pdf_bytes):
        """Extract text and tables from PDF"""
        pdf_file = BytesIO(pdf_bytes)
        text_data = []
        tables = []
        
        # Try pdfplumber first (better for tables)
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        text_data.append(f"=== Page {page_num} ===\n{text}")
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_idx, table in enumerate(page_tables):
                            if table and len(table) > 0:
                                try:
                                    # First row as headers
                                    headers = table[0]
                                    data_rows = table[1:]
                                    df = pd.DataFrame(data_rows, columns=headers)
                                    tables.append({
                                        "page": page_num,
                                        "table_number": table_idx + 1,
                                        "data": df
                                    })
                                    print(f"  → Extracted table {table_idx + 1} from page {page_num}")
                                except Exception as e:
                                    print(f"  → Could not parse table {table_idx + 1}: {e}")
        except Exception as e:
            # Fallback to PyPDF2
            print(f"  → pdfplumber failed, using PyPDF2: {e}")
            pdf_file.seek(0)
            try:
                reader = PyPDF2.PdfReader(pdf_file)
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_data.append(f"=== Page {page_num} ===\n{text}")
            except Exception as e2:
                print(f"  → PyPDF2 also failed: {e2}")
        
        return {
            "text": "\n\n".join(text_data),
            "tables": tables
        }
    
    async def process_and_analyze(self, data, task_description: str):
        """Process data and perform analysis based on task"""
        
        # Convert data to a format LLM can work with
        data_str = self._format_data_for_llm(data)
        
        # Use LLM to analyze
        analysis_prompt = f"""You are a data analyst. Analyze the data and answer the question precisely.

TASK: {task_description}

DATA:
{data_str}

INSTRUCTIONS:
1. Read the task carefully
2. Analyze the provided data
3. Calculate or extract the required information
4. Provide ONLY the final answer
5. If it's a number, provide just the number (no commas, no units unless specified)
6. If it's text, provide just the text
7. Do NOT include explanations or reasoning

ANSWER:"""
        
        result = await self.llm.query(analysis_prompt)
        
        # Extract just the answer
        return self._extract_answer(result)
    
    def _format_data_for_llm(self, data) -> str:
        """Format data for LLM consumption"""
        if isinstance(data, pd.DataFrame):
            data_str = f"DATAFRAME ({len(data)} rows × {len(data.columns)} columns)\n\n"
            data_str += f"Columns: {list(data.columns)}\n\n"
            data_str += "Data:\n"
            data_str += data.to_string(max_rows=100, max_cols=20)
            return data_str
        
        elif isinstance(data, dict) and 'tables' in data:
            data_str = f"PDF DOCUMENT\n\n"
            
            # Include text content
            if data['text']:
                data_str += f"TEXT CONTENT:\n{data['text'][:2000]}\n\n"
            
            # Include tables
            if data['tables']:
                data_str += f"TABLES ({len(data['tables'])} found):\n\n"
                for i, table_info in enumerate(data['tables']):
                    data_str += f"--- Table {i+1} (Page {table_info['page']}) ---\n"
                    data_str += table_info['data'].to_string(max_rows=100)
                    data_str += "\n\n"
            
            return data_str
        
        elif isinstance(data, list):
            return json.dumps(data, indent=2)[:3000]
        
        elif isinstance(data, dict):
            return json.dumps(data, indent=2)[:3000]
        
        else:
            return str(data)[:3000]
    
    def _extract_answer(self, llm_response: str):
        """Extract the actual answer from LLM response"""
        # Remove common prefixes and clean up
        response = llm_response.strip()
        
        # Remove markdown code blocks
        response = re.sub(r'```[a-z]*\n', '', response)
        response = response.replace('```', '')
        
        # Remove common answer prefixes
        response = re.sub(
            r'^(Answer:|Result:|The answer is:?|Final answer:?|ANSWER:)\s*',
            '',
            response,
            flags=re.IGNORECASE
        )
        
        # Try to find numbers if it looks like a numeric answer
        lines = response.split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line:
                # Check if it's a pure number (possibly with decimal)
                try:
                    # Remove commas and try to parse
                    clean_num = line.replace(',', '').replace(' ', '')
                    float(clean_num)
                    return clean_num
                except:
                    pass
        
        # Return the last non-empty line or the whole response
        for line in reversed(lines):
            if line.strip():
                return line.strip()
        
        return response.strip()