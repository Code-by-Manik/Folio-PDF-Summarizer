import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from langchain_core.documents import Document
from app import split_documents


class BackendTests(unittest.TestCase):
    def test_split_documents_preserves_content(self):
        text = (
            "First paragraph.\n\n"
            "Second paragraph.\n\n"
            "Third paragraph."
        )

        document = Document(
            page_content=text,
            metadata={"source": "sample.pdf", "page": 1},
        )

        chunks = split_documents([document])

        self.assertGreaterEqual(len(chunks), 1)

        combined_text = "\n".join(
            chunk.page_content for chunk in chunks
        )

        self.assertIn("First paragraph.", combined_text)
        self.assertIn("Second paragraph.", combined_text)
        self.assertIn("Third paragraph.", combined_text)

    def test_split_documents_preserves_metadata(self):
        document = Document(
            page_content="Example PDF content.",
            metadata={"source": "sample.pdf", "page": 3},
        )

        chunks = split_documents([document])

        self.assertTrue(chunks)
        self.assertEqual(chunks[0].metadata["source"], "sample.pdf")
        self.assertEqual(chunks[0].metadata["page"], 3)

    def test_split_documents_handles_empty_input(self):
        chunks = split_documents([])

        self.assertEqual(chunks, [])


    def test_home_page_returns_success(self):
        from app import app

        app.config["TESTING"] = True

        with app.test_client() as client:
            response = client.get("/")
            self.assertEqual(response.status_code, 200)

    def test_chat_without_uploaded_pdf_returns_bad_request(self):
        from app import app, rag_state

        app.config["TESTING"] = True

        with app.test_client() as client:
            with client.session_transaction() as flask_session:
                flask_session["guest_token"] = "test-guest-no-pdf"

            response = client.post(
                "/api/chat",
                json={"message": "Summarize my document"},
            )

            self.assertEqual(response.status_code, 400)
            self.assertIn(
                "upload a pdf",
                response.get_json()["error"].lower(),
            )


if __name__ == "__main__":
    unittest.main()