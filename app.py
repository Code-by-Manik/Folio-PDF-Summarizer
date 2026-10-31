import hashlib
import json
import os
import shutil
import traceback
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# LangChain & Vector Store Dependencies
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# ===========================================================================
# 1. ENVIRONMENT & FLASK CONFIGURATION
# ===========================================================================

load_dotenv(override=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash").strip()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploaded_pdfs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

PROFILE_PICS_FOLDER = os.path.join(os.path.dirname(__file__), "static", "profile_pics")
os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)

FAISS_INDICES_FOLDER = os.path.join(os.path.dirname(__file__), "faiss_indices")
os.makedirs(FAISS_INDICES_FOLDER, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB limit
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


def get_file_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


# Global JSON Error Handler
@app.errorhandler(Exception)
def handle_unexpected_error(e):
    traceback.print_exc()
    return jsonify({"error": str(e) or "An internal server error occurred."}), 500


# ===========================================================================
# 2. DATABASE MODELS & HELPER UTILITIES
# ===========================================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_pic = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sessions = db.relationship("ChatSession", backref="user", lazy=True, cascade="all, delete-orphan")


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    guest_token = db.Column(db.String(64), nullable=True)
    title = db.Column(db.String(150), nullable=False, default="New Conversation")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    messages = db.relationship("ChatMessage", backref="session", lazy=True, cascade="all, delete-orphan")


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("chat_sessions.id"), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.Text, nullable=True)        # Stored as JSON string
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


with app.app_context():
    db.create_all()


def get_or_create_guest_token():
    if "guest_token" not in session:
        session["guest_token"] = str(uuid.uuid4())
    return session["guest_token"]


def get_owner_key():
    """Generates a unique isolation key per user or guest session."""
    user_id = session.get("user_id")
    if user_id:
        return f"user_{user_id}"
    return f"guest_{get_or_create_guest_token()}"


# ===========================================================================
# 3. EMBEDDING & LLM SETUP
# ===========================================================================

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

llm = None
if OPENROUTER_API_KEY:
    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.2,
        max_tokens=2000,
    )

STANDARD_RAG_PROMPT = """You are an intelligent document search assistant answering questions about uploaded PDF documents.

Use the provided context below to answer the user's question accurately and thoroughly. 
Infer logically from the context where appropriate.

If the provided context does not contain enough relevant information, state clearly:
"I could not find this information in the provided document(s)."

{chat_history}

Context:
{context}

Question:
{question}

Answer:
"""

STRUCTURED_SUMMARY_PROMPT = """You are an expert document analyst.

Generate a clear, well-structured response based on the document context below.

Formatting Instructions:
1. If the user explicitly requests a brief response, adhere to their requested length.
2. Otherwise, structure the answer clearly using Markdown headings and bullets.

{chat_history}

Document Context:
{context}

User Request:
{question}

Answer:"""

SUMMARY_KEYWORDS = [
    "summarize", "summarise", "summary", "overview", "what is this document about",
    "main topic", "abstract", "title", "give title", "heading", "tldr", "synopsis",
    "author", "authors", "affiliation", "institution", "objective", "objectives",
    "purpose", "aim", "research question", "finding", "findings", "conclusion", "conclusions"
]


def is_summary_query(query: str) -> bool:
    q = query.lower().strip()
    return any(keyword in q for keyword in SUMMARY_KEYWORDS)


# ===========================================================================
# 4. RAG & SESSION-SCOPED VECTOR SEARCH LOGIC
# ===========================================================================

rag_state = {}  # In-memory lookup: owner_key -> retriever


def get_retriever_for_owner(owner_key):
    """Fetches in-memory retriever or loads owner-specific FAISS index from disk."""
    if owner_key in rag_state and rag_state[owner_key] is not None:
        return rag_state[owner_key]

    owner_index_path = os.path.join(FAISS_INDICES_FOLDER, owner_key)
    index_file = os.path.join(owner_index_path, "index.faiss")

    if os.path.exists(owner_index_path) and os.path.exists(index_file):
        try:
            vector_store = FAISS.load_local(
                owner_index_path, embedding_model, allow_dangerous_deserialization=True
            )
            retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 8})
            rag_state[owner_key] = retriever
            return retriever
        except Exception as e:
            print(f"Could not load FAISS index for {owner_key}:", e)

    return None


def load_pdfs(pdf_paths):
    all_documents = []
    for path in pdf_paths:
        if not os.path.exists(path):
            continue
        file_name = os.path.basename(path)
        extracted_chars = 0

        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(path) as pdf:
                    for page_number, page in enumerate(pdf.pages, start=1):
                        text = page.extract_text() or ""
                        if text.strip():
                            extracted_chars += len(text)
                            all_documents.append(
                                Document(page_content=text, metadata={"source": file_name, "page": page_number})
                            )
            except Exception:
                extracted_chars = 0

        if extracted_chars == 0:
            try:
                reader = PdfReader(path)
                for page_number, page in enumerate(reader.pages, start=1):
                    text = page.extract_text() or ""
                    if text.strip():
                        extracted_chars += len(text)
                        all_documents.append(
                            Document(page_content=text, metadata={"source": file_name, "page": page_number})
                        )
            except Exception as pypdf_err:
                print(f"[pypdf] Extraction error: {pypdf_err}")

    return all_documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150, separators=["\n\n", "\n", ". ", " ", ""])
    return splitter.split_documents(documents)


def format_context(chunks):
    formatted_parts = []
    for i, doc in enumerate(chunks, start=1):
        source = doc.metadata.get("source", "Unknown File")
        page = doc.metadata.get("page", "?")
        formatted_parts.append(f"[Chunk {i} | Source: {source} | Page: {page}]\n{doc.page_content}")
    return "\n\n".join(formatted_parts)


def parse_llm_response(response_content):
    if isinstance(response_content, str):
        return response_content
    elif isinstance(response_content, list):
        return "\n".join([str(item) for item in response_content])
    return str(response_content)


def get_document_intro_chunks(retriever, query):
    try:
        docstore = getattr(retriever.vectorstore, "docstore", None)
        if docstore and hasattr(docstore, "_dict") and docstore._dict:
            all_chunks = list(docstore._dict.values())
            intro_chunks = all_chunks[:4]
            outro_chunks = all_chunks[-2:] if len(all_chunks) > 4 else []
            return intro_chunks + outro_chunks
    except Exception:
        pass
    return retriever.vectorstore.similarity_search("author objective purpose finding conclusion abstract", k=8)


def answer_question(raw_question, retriever, llm_instance, history=None):
    if not llm_instance:
        return "Error: OPENROUTER_API_KEY is not configured in your .env file.", []

    try:
        if is_summary_query(raw_question):
            results = get_document_intro_chunks(retriever, raw_question)
        else:
            results = retriever.invoke(raw_question)
    except Exception as e:
        return f"Retrieval Error: {e}", []

    if not results:
        return "No relevant information found in the uploaded document(s).", []

    context_text = format_context(results)
    formatted_history = ""
    if history:
        history_lines = [f"User: {turn['question']}\nAssistant: {turn['answer']}" for turn in history[-3:]]
        formatted_history = "Previous Conversation:\n" + "\n".join(history_lines) + "\n\n"

    prompt_template = STRUCTURED_SUMMARY_PROMPT if is_summary_query(raw_question) else STANDARD_RAG_PROMPT
    prompt = prompt_template.format(chat_history=formatted_history, context=context_text, question=raw_question)

    try:
        response = llm_instance.invoke(prompt)
        answer = parse_llm_response(response.content)
    except Exception as e:
        answer = f"LLM Generation Error: {e}"

    return answer, results


# ===========================================================================
# 5. VIEW & PAGE ROUTES
# ===========================================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/profile")
def profile():
    return render_template("profile.html")


# ===========================================================================
# 6. AUTHENTICATION & USER PROFILE ENDPOINTS
# ===========================================================================

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required."}), 400
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({"error": "Username or Email already registered."}), 400

    new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    session["user_id"] = new_user.id
    return jsonify({"message": "Account created!", "username": new_user.username}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = data.get("username", "").strip()
    password = data.get("password", "")
    user = User.query.filter((User.username == identifier) | (User.email == identifier.lower())).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials."}), 401

    session["user_id"] = user.id
    return jsonify({"message": "Logged in!", "username": user.username}), 200


@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out."}), 200


@app.route("/api/me", methods=["GET"])
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 200

    user = db.session.get(User, user_id)
    if not user:
        session.pop("user_id", None)
        return jsonify({"authenticated": False}), 200

    return jsonify({"authenticated": True, "user_id": user.id, "username": user.username, "email": user.email}), 200


@app.route("/api/user/profile", methods=["GET"])
def get_user_profile_data():
    user_id = session.get("user_id")

    # Guests do not have persistent chat history.
    if not user_id:
        return jsonify({
            "username": "Guest User",
            "email": "guest@session",
            "created_at": "N/A",
            "total_sessions": 0,
            "profile_pic": None,
            "history": []
        }), 200

    user = db.session.get(User, user_id)

    if not user:
        session.pop("user_id", None)
        return jsonify({
            "username": "Guest User",
            "email": "guest@session",
            "created_at": "N/A",
            "total_sessions": 0,
            "profile_pic": None,
            "history": []
        }), 200

    user_sessions = (
        ChatSession.query
        .filter_by(user_id=user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )

    history = []

    for s in user_sessions:
        msg_count = ChatMessage.query.filter_by(
            session_id=s.id
        ).count()

        history.append({
            "id": s.id,
            "title": s.title,
            "updated_at": (
                s.updated_at.strftime("%b %d, %Y")
                if s.updated_at else "N/A"
            ),
            "message_count": msg_count
        })

    return jsonify({
        "username": user.username,
        "email": user.email,
        "created_at": (
            user.created_at.strftime("%B %d, %Y")
            if user.created_at else "N/A"
        ),
        "total_sessions": len(user_sessions),
        "profile_pic": user.profile_pic,
        "history": history
    }), 200


@app.route("/api/user/profile-pic", methods=["POST"])
def upload_profile_picture():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if "pfp" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["pfp"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return jsonify({"error": "Invalid image format"}), 400

    filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
    file_path = os.path.join(PROFILE_PICS_FOLDER, filename)
    file.save(file_path)

    public_url = f"/static/profile_pics/{filename}"

    user = db.session.get(User, user_id)
    user.profile_pic = public_url
    db.session.commit()

    return jsonify({"profile_pic": public_url}), 200


# ===========================================================================
# 7. CHAT SESSIONS & MESSAGES ENDPOINTS
# ===========================================================================

@app.route("/api/sessions", methods=["GET"])
def get_sessions():
    user_id = session.get("user_id")
    guest_token = get_or_create_guest_token()

    if user_id:
        sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()
    else:
        sessions = ChatSession.query.filter_by(guest_token=guest_token).order_by(ChatSession.updated_at.desc()).all()

    return jsonify({
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.strftime("%b %d, %Y") if s.created_at else "Recent",
                "updated_at": s.updated_at.strftime("%b %d, %H:%M") if s.updated_at else "Recent"
            } for s in sessions
        ]
    }), 200


@app.route("/api/sessions", methods=["POST"])
def create_session():
    user_id = session.get("user_id")
    guest_token = get_or_create_guest_token()

    new_session = ChatSession(
        user_id=user_id,
        guest_token=guest_token if not user_id else None,
        title="New Conversation"
    )
    db.session.add(new_session)
    db.session.commit()

    return jsonify({"session_id": new_session.id, "title": new_session.title}), 201


@app.route("/api/sessions/<session_id>", methods=["GET"])
@app.route("/api/sessions/<session_id>/messages", methods=["GET"])
def get_session_messages(session_id):
    user_id = session.get("user_id")
    guest_token = get_or_create_guest_token()

    chat_sess = ChatSession.query.filter_by(id=session_id).first()

    if not chat_sess:
        return jsonify({"error": "Conversation not found."}), 404

    # Authorization Check
    if user_id:
        if chat_sess.user_id != user_id:
            return jsonify({"error": "Unauthorized access."}), 403
    else:
        if chat_sess.guest_token != guest_token:
            return jsonify({"error": "Unauthorized access."}), 403

    messages = (
        ChatMessage.query
        .filter_by(session_id=session_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    formatted_messages = []

    for msg in messages:
        formatted_messages.append({
            "sender": msg.sender,
            "role": "user" if msg.sender == "user" else "assistant",
            "content": msg.content,
            "text": msg.content,
            "sources": json.loads(msg.sources) if msg.sources else []
        })

    return jsonify({
        "session_id": chat_sess.id,
        "title": chat_sess.title,
        "session": {
            "id": chat_sess.id,
            "title": chat_sess.title
        },
        "messages": formatted_messages
    }), 200


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    user_id = session.get("user_id")
    guest_token = get_or_create_guest_token()

    chat_sess = ChatSession.query.filter_by(id=session_id).first()

    if not chat_sess:
        return jsonify({"error": "Conversation not found."}), 404

    if user_id:
        if chat_sess.user_id != user_id:
            return jsonify({"error": "Unauthorized access."}), 403
    else:
        if chat_sess.guest_token != guest_token:
            return jsonify({"error": "Unauthorized access."}), 403

    db.session.delete(chat_sess)
    db.session.commit()

    return jsonify({"message": "Session deleted."}), 200


# ===========================================================================
# 8. UPLOAD & CHAT PROCESSING
# ===========================================================================

@app.route("/api/upload", methods=["POST"])
def upload_and_process_pdfs():
    if "files" not in request.files:
        return jsonify({"error": "No file payload received"}), 400

    files = request.files.getlist("files")
    temp_paths = []
    original_names = []
    owner_key = get_owner_key()

    try:
        # 1. Save uploads temporarily
        for file in files:
            if file and file.filename and file.filename.lower().endswith(".pdf"):
                safe_name = secure_filename(file.filename)

                if not safe_name:
                    continue

                temp_filename = f"_pending_{uuid.uuid4()}_{safe_name}"
                temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)

                file.save(temp_path)

                temp_paths.append(temp_path)
                original_names.append(safe_name)

        if not temp_paths:
            return jsonify({"error": "No valid PDF files uploaded."}), 400

        # 2. Extract PDF text
        docs = load_pdfs(temp_paths)

        if not docs:
            return jsonify({
                "error": (
                    "Could not extract text from the provided PDF(s). "
                    "File may be empty or image-only."
                )
            }), 400

        # 3. Split into chunks
        chunks = split_documents(docs)

        if not chunks:
            return jsonify({
                "error": "No text chunks could be created from the PDF."
            }), 400

        # 4. Add documents to the owner-isolated FAISS index
        owner_index_path = os.path.join(FAISS_INDICES_FOLDER, owner_key)
        index_file = os.path.join(owner_index_path, "index.faiss")

        if os.path.exists(index_file):
            vector_store = FAISS.load_local(
                owner_index_path,
                embedding_model,
                allow_dangerous_deserialization=True,
            )
            vector_store.add_documents(chunks)
        else:
            vector_store = FAISS.from_documents(chunks, embedding_model)

        vector_store.save_local(owner_index_path)

        # 5. Cleanup temporary uploaded PDFs
        for temp_path, original_name in zip(temp_paths, original_names):
            final_filename = f"{owner_key}_{uuid.uuid4().hex[:8]}_{original_name}"
            final_path = os.path.join(UPLOAD_FOLDER, final_filename)
            os.replace(temp_path, final_path)

        # 6. Update Owner Retriever in rag_state
        rag_state[owner_key] = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 8}
        )

        return jsonify({
            "message": "PDF indexed successfully.",
            "pages_extracted": len(docs),
            "chunks_created": len(chunks)
        }), 200

    except Exception as e:
        traceback.print_exc()

        for temp_path in temp_paths:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass

        return jsonify({
            "error": f"PDF processing failed: {e}"
        }), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    owner_key = get_owner_key()
    retriever = get_retriever_for_owner(owner_key)

    if retriever is None:
        return jsonify({
            "error": "Please upload a PDF document before asking questions."
        }), 400

    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id")

    if not user_message:
        return jsonify({
            "error": "Query message cannot be empty"
        }), 400

    user_id = session.get("user_id")

    # LOGGED-IN USERS
    if user_id:
        chat_sess = None

        if session_id:
            chat_sess = db.session.get(ChatSession, session_id)

            if chat_sess and chat_sess.user_id != user_id:
                chat_sess = None

        if not chat_sess:
            chat_sess = ChatSession(
                user_id=user_id,
                guest_token=None,
                title=user_message[:30] + (
                    "..." if len(user_message) > 30 else ""
                )
            )

            db.session.add(chat_sess)
            db.session.commit()

        elif chat_sess.title == "New Conversation":
            chat_sess.title = user_message[:30] + (
                "..." if len(user_message) > 30 else ""
            )

        db.session.add(
            ChatMessage(
                session_id=chat_sess.id,
                sender="user",
                content=user_message
            )
        )

        db.session.commit()

        past_messages = (
            ChatMessage.query
            .filter_by(session_id=chat_sess.id)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )

    # GUEST USERS
    else:
        chat_sess = None
        past_messages = []

    # BUILD CHAT HISTORY
    history = []

    for i in range(0, len(past_messages) - 1, 2):
        if i + 1 < len(past_messages):
            history.append({
                "question": past_messages[i].content,
                "answer": past_messages[i + 1].content
            })

    answer, sources = answer_question(
        user_message,
        retriever,
        llm,
        history
    )

    # FORMAT / DEDUPLICATE SOURCES
    formatted_sources = []
    seen_sources = set()

    for doc in sources:
        raw_source = doc.metadata.get("source", "Unknown")

        clean_name = (
            raw_source.split("_", 1)[-1]
            if "_" in raw_source
            else raw_source
        )

        page = doc.metadata.get("page")

        source_key = (clean_name, page)

        if source_key not in seen_sources:
            seen_sources.add(source_key)

            formatted_sources.append({
                "source": clean_name,
                "page": page
            })

    # SAVE BOT RESPONSE ONLY FOR LOGGED-IN USERS
    if user_id:
        db.session.add(
            ChatMessage(
                session_id=chat_sess.id,
                sender="bot",
                content=answer,
                sources=(
                    json.dumps(formatted_sources)
                    if formatted_sources
                    else None
                )
            )
        )

        chat_sess.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        response_session_id = chat_sess.id
        response_session_title = chat_sess.title

    else:
        response_session_id = None
        response_session_title = "New Conversation"

    return jsonify({
        "session_id": response_session_id,
        "session_title": response_session_title,
        "answer": answer,
        "sources": formatted_sources
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)