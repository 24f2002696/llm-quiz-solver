\# LLM Quiz Solver



Automated quiz solver using Google Gemini 2.5 Flash for data analysis tasks.



\## Features

\- Automatic quiz chain solving

\- JavaScript-rendered page handling (Playwright)

\- PDF, CSV, Excel, JSON data processing

\- LLM-powered data analysis

\- 3-minute timeout handling per quiz



\## Technologies

\- \*\*FastAPI\*\* - Web framework

\- \*\*Google Gemini 2.5 Flash\*\* - LLM for reasoning and analysis

\- \*\*Playwright\*\* - JavaScript rendering

\- \*\*Pandas\*\* - Data processing

\- \*\*pdfplumber/PyPDF2\*\* - PDF extraction



\## Setup Locally



1\. Clone repository:

```bash

git clone https://github.com/YOUR\_USERNAME/llm-quiz-solver.git

cd llm-quiz-solver

```



2\. Create virtual environment:

```bash

python -m venv venv

venv\\Scripts\\activate  # Windows

```



3\. Install dependencies:

```bash

pip install -r requirements.txt

python -m playwright install chromium

```



4\. Create `.env` file:

```bash

GEMINI\_API\_KEY=api\_key\_here

SECRET\_STRING=JCJGTMATBRSHSSDRHHKSIPPP

STUDENT\_EMAIL=24f2002696@ds.study.iitm.ac.in```



5\. Run locally:

```bash

python app.py

```



\## API Endpoints



\### POST /solve

Receive and solve quiz tasks.



\*\*Request:\*\*

```json

{

&nbsp; "email": "24f2002696@ds.study.iitm.ac.in",

&nbsp; "secret": "JCJGTMATBRSHSSDRHHKSIPPP",

&nbsp; "url": "https://example.com/quiz-123"

}

```



\*\*Response:\*\*

```json

{

&nbsp; "status": "success",

&nbsp; "message": "Quiz solving completed",

&nbsp; "result": {

&nbsp;   "questions\_solved": 5

&nbsp; }

}

```



\### GET /

Health check and API info



\### GET /health

Service health status



\## Deployment



Deployed on Railway.app with automatic deployments from main branch.



\*\*Live URL:\*\* `https://your-app.railway.app`



\## Project Structure

```bash

llm-quiz-solver/

├── app.py              # FastAPI application

├── quiz\_solver.py      # Main quiz solving logic

├── llm\_handler.py      # Gemini API integration

├── data\_processor.py   # Data parsing and analysis

├── requirements.txt    # Python dependencies

├── .env               # Environment variables (not in repo)

├── .gitignore         # Git ignore rules

└── README.md          # This file

```



\## Environment Variables



\- `GEMINI\_API\_KEY` - Google Gemini API key

\- `SECRET\_STRING` - Secret for request verification

\- `STUDENT\_EMAIL` - Student email for verification

\- `PORT` - Port number (set by Railway)



\## Author



IIT Madras BS Student

Email: 24f2002696@ds.study.iitm.ac.in









