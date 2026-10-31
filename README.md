

\# Folio – AI-Powered PDF Summarizer \& Question Answering Assistant



Folio is an AI-powered PDF assistant that allows users to upload PDF documents, generate summaries, and ask questions using Retrieval-Augmented Generation (RAG).



Instead of manually searching through lengthy documents, users can interact with their PDFs through a conversational interface and receive context-aware answers.



\## Features



\- \*\*PDF Upload:\*\* Upload PDF documents for processing.

\- \*\*AI-Powered Summarization:\*\* Generate concise summaries of document content.

\- \*\*Conversational Q\&A:\*\* Ask questions about uploaded documents in natural language.

\- \*\*Retrieval-Augmented Generation (RAG):\*\* Retrieve relevant document chunks to ground AI-generated responses.

\- \*\*Vector Search:\*\* Use FAISS for efficient similarity search.

\- \*\*Semantic Embeddings:\*\* Generate document embeddings using Hugging Face Sentence Transformers.

\- \*\*User Authentication:\*\* Sign up, log in, and manage user sessions.

\- \*\*Chat History:\*\* Manage saved conversations.

\- \*\*Profile Management:\*\* Maintain user profile information.



\## Tech Stack



| Category | Technologies |

|---|---|

| Backend | Python, Flask |

| Frontend | HTML, CSS, JavaScript |

| AI / LLM | Gemini via OpenRouter |

| RAG Framework | LangChain |

| Embeddings | Hugging Face Sentence Transformers |

| Vector Database | FAISS |

| PDF Processing | PyPDF |

| Database | SQLite, Flask-SQLAlchemy |

| Testing | Pytest |



\## RAG Architecture



1\. \*\*Document Ingestion:\*\* Extract text from uploaded PDF files.

2\. \*\*Text Splitting:\*\* Divide extracted text into smaller overlapping chunks.

3\. \*\*Embedding Generation:\*\* Convert text chunks into vector embeddings.

4\. \*\*Vector Storage:\*\* Store embeddings in a FAISS index.

5\. \*\*Retrieval:\*\* Retrieve relevant chunks based on the user's question.

6\. \*\*Response Generation:\*\* Pass retrieved context to the language model to generate an answer.



```text

&#x20;      PDF Upload

&#x20;          |

&#x20;          v

&#x20;     Text Extraction

&#x20;          |

&#x20;          v

&#x20;      Text Splitting

&#x20;          |

&#x20;          v

&#x20;  Hugging Face Embeddings

&#x20;          |

&#x20;          v

&#x20;      FAISS Index

&#x20;          |

&#x20;          v

&#x20;     User Question

&#x20;          |

&#x20;          v

&#x20;  Semantic Retrieval

&#x20;          |

&#x20;          v

&#x20;  Retrieved Context

&#x20;          |

&#x20;          v

&#x20;  Gemini via OpenRouter

&#x20;          |

&#x20;          v

&#x20;    AI-Generated Answer

```



\## Installation \& Setup



\### 1. Clone the repository



```bash

git clone https://github.com/Code-by-Manik/Folio-PDF-Summarizer.git

cd Folio-PDF-Summarizer

```



\### 2. Create a virtual environment



```bash

python -m venv .venv

```



Activate it on Windows:



```powershell

.venv\\Scripts\\Activate.ps1

```



\### 3. Install dependencies



```bash

pip install -r requirements.txt

```



\### 4. Configure environment variables



Create a `.env` file in the project root:



```env

OPENROUTER\_API\_KEY=your\_openrouter\_api\_key

OPENROUTER\_MODEL=google/gemini-2.5-flash

SECRET\_KEY=replace\_with\_a\_secure\_random\_secret

```



Get an API key from \[OpenRouter](https://openrouter.ai/).



Never commit your `.env` file or expose API keys publicly.



\### 5. Run the application



```bash

python app.py

```



Open the local application in your browser at:



`http://127.0.0.1:5000`



\## Running Tests



```bash

python -m pytest tests/ -v

```



\## Project Structure



```text

Folio-PDF-Summarizer/

│

├── app.py

├── requirements.txt

├── .gitignore

├── run\_backend.bat

├── test\_app.py

├── verify\_backend.py

│

├── notebooks/

│   └── AI\_PDF\_QA\_RAG\_Gemini.ipynb

│

├── static/

│   ├── app.js

│   └── style.css

│

├── templates/

│   ├── Index.html

│   └── profile.html

│

└── tests/

&#x20;   └── test\_backend.py

```



\## Future Improvements



\- Cloud deployment and persistent document storage.

\- Improved multi-document retrieval.

\- More detailed source references in generated answers.

\- Enhanced document comparison and analysis.

\- Improved production security and scalability.



\## Author



\*\*Manik Aggarwal\*\*



GitHub: \[@Code-by-Manik](https://github.com/Code-by-Manik)



\---



\*Folio — Making document understanding faster and smarter.\*



