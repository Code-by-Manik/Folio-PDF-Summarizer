# # # import os
# # # import sys
# # # from dotenv import load_dotenv

# # # print("=" * 80)
# # # print("PYTHON")
# # # print("=" * 80)
# # # print("Python:", sys.version)

# # # print("\nCurrent directory:")
# # # print(os.getcwd())

# # # print("\nLoading .env...")
# # # load_dotenv()

# # # api_key = os.getenv("GOOGLE_API_KEY")

# # # print("\nAPI KEY")
# # # print("-" * 80)

# # # if api_key is None:
# # #     print("❌ GOOGLE_API_KEY not found")
# # # else:
# # #     print("Loaded successfully")
# # #     print("Length:", len(api_key))
# # #     print("Starts with:", api_key[:10])
# # #     print("Ends with:", api_key[-6:])

# # # print("\n" + "=" * 80)
# # # print("PACKAGE VERSIONS")
# # # print("=" * 80)

# # # packages = [
# # #     "google-genai",
# # #     "google-generativeai",
# # #     "langchain-google-genai",
# # #     "langchain",
# # #     "transformers"
# # # ]

# # # try:
# # #     import importlib.metadata as metadata

# # #     for pkg in packages:
# # #         try:
# # #             print(f"{pkg}: {metadata.version(pkg)}")
# # #         except:
# # #             print(f"{pkg}: NOT INSTALLED")
# # # except Exception as e:
# # #     print(e)

# # # print("\n" + "=" * 80)
# # # print("GOOGLE GENAI TEST")
# # # print("=" * 80)

# # # try:
# # #     from google import genai

# # #     client = genai.Client(api_key=api_key)

# # #     print("Client created successfully.")

# # #     print("\nListing models...\n")

# # #     count = 0

# # #     for model in client.models.list():
# # #         print(model.name)
# # #         count += 1

# # #         if count >= 20:
# # #             break

# # #     print(f"\nPrinted first {count} models.")

# # # except Exception as e:
# # #     print("\nFAILED")
# # #     print(type(e).__name__)
# # #     print(e)

# # # print("\n" + "=" * 80)
# # # print("LANGCHAIN TEST")
# # # print("=" * 80)

# # # try:
# # #     from langchain_google_genai import ChatGoogleGenerativeAI

# # #     llm = ChatGoogleGenerativeAI(
# # #         model="gemini-2.5-flash",
# # #         google_api_key=api_key,
# # #         temperature=0
# # #     )

# # #     print("LLM created.")

# # #     response = llm.invoke("Reply with exactly one word: hello")

# # #     print("\nResponse:")
# # #     print(response.content)

# # # except Exception as e:
# # #     print("\nFAILED")
# # #     print(type(e).__name__)
# # #     print(e)

# # # print("\n" + "=" * 80)
# # # print("DONE")
# # # print("=" * 80)


# # from dotenv import load_dotenv
# # import os

# # load_dotenv()

# # from langchain_google_genai import ChatGoogleGenerativeAI

# # llm = ChatGoogleGenerativeAI(
# #     model="gemini-2.5-flash",
# #     google_api_key=os.getenv("GOOGLE_API_KEY"),
# # )

# # print("Model:", llm.model)

# # response = llm.invoke("Say hello")

# # print(response)

# from google import genai
# from dotenv import load_dotenv
# import os

# load_dotenv()

# client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents="Say hello"
# )

# print(response.text)


# from google import genai
# from dotenv import load_dotenv
# import os

# load_dotenv()

# client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# MODEL = "gemini-2.0-flash-001"   # <-- change only this line

# print("Testing:", MODEL)

# response = client.models.generate_content(
#     model=MODEL,
#     contents="Say hello in one sentence."
# )

# print(response.text)


# import os
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI

# load_dotenv()
# api_key = os.getenv("GOOGLE_API_KEY")

# print(f"Loaded Key: {api_key[:6]}...{api_key[-4:] if api_key else 'NONE'}")

# try:
#     llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
#     response = llm.invoke("Say hello")
#     print("SUCCESS:", response.content)
# except Exception as e:
#     print("FAILED:", e)

# import os
# from dotenv import load_dotenv
# from google import genai

# load_dotenv()
# api_key = os.getenv("GOOGLE_API_KEY")

# print(f"Loaded Key: {api_key[:6]}...{api_key[-4:] if api_key else 'NONE'}")

# try:
#     client = genai.Client(api_key=api_key)
#     response = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents="Say hello",
#     )
#     print("SUCCESS:", response.text)
# except Exception as e:
#     print("FAILED:", e)



# import os
# from dotenv import load_dotenv
# from google import genai

# load_dotenv(override=True)

# key = os.getenv("GOOGLE_API_KEY")

# print("Key loaded:", bool(key))
# print("Prefix:", key[:3] if key else None)
# print("Length:", len(key) if key else 0)

# client = genai.Client(api_key=key)

# print("\nTesting Gemini...")

# response = client.models.generate_content(
#     model="gemini-2.0-flash",
#     contents="Reply with exactly: READY"
# )

# print("\nSUCCESS:")
# print(response.text)



# import os
# from dotenv import load_dotenv
# from google import genai

# print("=" * 70)
# print("GEMINI AUTHENTICATION TEST")
# print("=" * 70)

# # Load .env
# load_dotenv(override=True)

# api_key = os.getenv("GOOGLE_API_KEY")

# print("\nKey loaded:", bool(api_key))

# if not api_key:
#     raise RuntimeError("GOOGLE_API_KEY was not found in .env")

# print("Key prefix:", api_key[:3])
# print("Key length:", len(api_key))

# print("\nCreating Gemini client...")

# client = genai.Client(
#     api_key=api_key
# )

# print("Client created.")

# print("\nTesting models.list()...")

# try:
#     models = client.models.list()

#     for i, model in enumerate(models):
#         print(model.name)

#         if i >= 10:
#             break

#     print("\nModel listing worked.")

# except Exception as e:
#     print("\nMODEL LIST FAILED:")
#     print(type(e).__name__)
#     print(e)

# print("\n" + "=" * 70)
# print("TESTING GENERATE CONTENT")
# print("=" * 70)

# try:
#     response = client.models.generate_content(
#         model="gemini-2.0-flash",
#         contents="Reply with exactly one word: READY"
#     )

#     print("\nSUCCESS!")
#     print("Response:")
#     print(response.text)

# except Exception as e:
#     print("\nGENERATE CONTENT FAILED:")
#     print(type(e).__name__)
#     print(e)

# print("\n" + "=" * 70)
# print("DONE")
# print("=" * 70)



# import os
# from dotenv import load_dotenv
# from google import genai

# print("=" * 70)
# print("AQ KEY TEST")
# print("=" * 70)

# load_dotenv()

# key = os.getenv("GOOGLE_API_KEY")

# print("Key loaded:", bool(key))

# if key:
#     print("Prefix:", key[:3])
#     print("Length:", len(key))

# if not key:
#     raise RuntimeError("GOOGLE_API_KEY was not loaded.")

# print("\nCreating client...")

# client = genai.Client(
#     api_key=key
# )

# print("Client created.")

# print("\nTesting Gemini API...")

# try:
#     response = client.models.generate_content(
#         model="gemini-flash-latest",
#         contents="Reply with exactly: HELLO"
#     )

#     print("\nSUCCESS!")
#     print("-" * 70)
#     print(response.text)

# except Exception as e:
#     print("\nFAILED!")
#     print("-" * 70)
#     print(type(e).__name__)
#     print(e)

# print("\n" + "=" * 70)



# import os
# from dotenv import load_dotenv
# from google import genai

# print("=" * 70)
# print("GEMINI AQ KEY TEST")
# print("=" * 70)

# # Load .env
# load_dotenv(override=True)

# key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# if not key:
#     print("❌ No API key found.")
#     raise SystemExit(1)

# print("Key loaded:", True)
# print("Prefix:", key[:3])
# print("Length:", len(key))

# print("\nCreating client...")

# try:
#     client = genai.Client(api_key=key)
#     print("Client created successfully.")
# except Exception as e:
#     print("❌ Client creation failed:")
#     print(type(e).__name__)
#     print(e)
#     raise SystemExit(1)

# print("\nTesting generate_content...")
# print("-" * 70)

# try:
#     response = client.models.generate_content(
#         model="gemini-flash-latest",
#         contents="Reply with exactly: HELLO"
#     )

#     print("✅ SUCCESS!")
#     print("Response:")
#     print(response.text)

# except Exception as e:
#     print("❌ FAILED")
#     print("-" * 70)
#     print(type(e).__name__)
#     print(e)

# print("\n" + "=" * 70)

# from google import genai

# print("=" * 70)
# print("DIRECT AQ KEY TEST")
# print("=" * 70)

# IMPORTANT:
# Temporarily paste the NEW AQ. key here for this test.
# Do NOT send the key to me.
# API_KEY = "PASTE_YOUR_AQ_KEY_HERE"

# print("Key prefix:", API_KEY[:3])
# print("Key length:", len(API_KEY))

# if not API_KEY.startswith("AQ."):
#     print("WARNING: This is not an AQ. key.")

# print("\nCreating client...")

# client = genai.Client(api_key=API_KEY)

# print("Client created.")

# print("\nCalling Gemini...")
# print("-" * 70)

# try:
#     response = client.models.generate_content(
#         model="gemini-3-flash-preview",
#         contents="Reply with exactly: HELLO"
#     )

#     print("SUCCESS!")
#     print("-" * 70)
#     print(response.text)

# except Exception as e:
#     print("FAILED!")
#     print("-" * 70)
#     print(type(e).__name__)
#     print(e)

# print("\n" + "=" * 70)
# print("TEST COMPLETE")
# print("=" * 70)

# import os
# import sys
# from dotenv import load_dotenv

# print("======================================================================", flush=True)
# print("DIRECT API KEY TEST", flush=True)
# print("======================================================================", flush=True)

# # 1. Load environment variables
# load_dotenv(override=True)
# api_key = os.getenv("GOOGLE_API_KEY", "").strip()

# print(f"Step 1: Checking API Key...", flush=True)
# if not api_key:
#     print("❌ ERROR: GOOGLE_API_KEY is missing or empty in your .env file!", flush=True)
#     sys.exit(1)

# print(f"✓ Key found: {api_key[:6]}... (Length: {len(api_key)})", flush=True)

# # 2. Test Gemini Connection directly
# print("\nStep 2: Connecting to Gemini API...", flush=True)
# try:
#     from langchain_google_genai import ChatGoogleGenerativeAI

#     llm = ChatGoogleGenerativeAI(
#         model="gemini-1.5-flash",
#         google_api_key=api_key,
#     )
    
#     response = llm.invoke("Hello, respond with 'API Key is working!'")
#     print("\n----------------------------------------------------------------------", flush=True)
#     print("SUCCESS RESPONSE FROM GEMINI:", flush=True)
#     print(response.content, flush=True)
#     print("----------------------------------------------------------------------", flush=True)

# except Exception as err:
#     print("\n❌ API TEST FAILED WITH EXCEPTION:", flush=True)
#     print(err, flush=True)


# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv(override=True)
# api_key = os.getenv("GOOGLE_API_KEY", "").strip()
# model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# print(f"Testing key: {api_key[:6]}...")

# url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
# headers = {"Content-Type": "application/json"}
# payload = {
#     "contents": [{"parts": [{"text": "Respond with 'Direct HTTP Success!'"}]}]
# }

# response = requests.post(url, headers=headers, json=payload)

# print("Status Code:", response.status_code)
# if response.status_code == 200:
#     print("Response:", response.json()["candidates"][0]["content"]["parts"][0]["text"])
# else:
#     print("Error:", response.text)

# import os
# import sys
# from dotenv import load_dotenv
# from langchain_openrouter import ChatOpenRouter

# print("======================================================================", flush=True)
# print("OPENROUTER API DIAGNOSTIC TEST", flush=True)
# print("======================================================================", flush=True)

# load_dotenv(override=True)

# api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
# model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash").strip()

# if not api_key:
#     print("❌ OPENROUTER_API_KEY is missing from your .env file!", flush=True)
#     sys.exit(1)

# print(f"Target Model: {model_name}", flush=True)
# print(f"Key Prefix: '{api_key[:10]}...' | Key Length: {len(api_key)}", flush=True)

# try:
#     llm = ChatOpenRouter(
#         model=model_name,
#         api_key=api_key,
#         temperature=0.2,
#     )
    
#     print(f"\nSending request to OpenRouter ({model_name})...", flush=True)
#     response = llm.invoke("Respond with 'OpenRouter connection successful!'")
    
#     print("\n----------------------------------------------------------------------", flush=True)
#     print("SUCCESS RESPONSE:", flush=True)
#     print(response.content, flush=True)
#     print("----------------------------------------------------------------------", flush=True)

# except Exception as err:
#     print("\n❌ OPENROUTER TEST FAILED:", flush=True)
#     print(err, flush=True)


import os
import sys
from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter

print("======================================================================", flush=True)
print("OPENROUTER API DIAGNOSTIC TEST", flush=True)
print("======================================================================", flush=True)

load_dotenv(override=True)

api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash").strip()

if not api_key:
    print("❌ OPENROUTER_API_KEY is missing from your .env file!", flush=True)
    sys.exit(1)

print(f"Target Model: {model_name}", flush=True)
print(f"Key Prefix: '{api_key[:10]}...' | Key Length: {len(api_key)}", flush=True)

try:
    llm = ChatOpenRouter(
        model=model_name,
        api_key=api_key,
        temperature=0.2,
        max_tokens=1000,  # Explicitly caps credit reservation on OpenRouter
    )
    
    print(f"\nSending request to OpenRouter ({model_name})...", flush=True)
    response = llm.invoke("Respond with 'OpenRouter connection successful!'")
    
    print("\n----------------------------------------------------------------------", flush=True)
    print("SUCCESS RESPONSE:", flush=True)
    print(response.content, flush=True)
    print("----------------------------------------------------------------------", flush=True)

except Exception as err:
    print("\n❌ OPENROUTER TEST FAILED:", flush=True)
    print(err, flush=True)