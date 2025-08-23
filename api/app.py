# FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.
from fastapi import FastAPI, Query  # Main FastAPI class and query parameter handling


from langchain.prompts import ChatPromptTemplate  # For building prompt templates for LLMs
from langchain_google_genai import ChatGoogleGenerativeAI  # Gemini model integration for LangChain
# from langserve import add_routes  # Utility to expose LangChain chains as API endpoints

# UVicorn is an ASGI server used to run FastAPI applications, handling HTTP requests asynchronously.
# (Asynchronous Server Gateway Interface)
import uvicorn  # ASGI server to run FastAPI apps

import os  # OS operations (env vars, paths)
from dotenv import load_dotenv  # Loads environment variables from .env file



load_dotenv()
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')

app = FastAPI(
    title="Langchain Server",
    version="1.0",
    description="A simple API Server with Gemini"
)

# -------------------------------
# Gemini Model
# -------------------------------
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Basic chat endpoint
# This endpoint exposes the Gemini model at /gemini/invoke
# add_routes(app, model, path="/gemini")

# -------------------------------
# Companion endpoint
# -------------------------------
@app.post("/companion")
async def companion(prompt: str, context: str = ""):
    try:
        # Single Gemini call: ask for answer and 25-word summary
        full_prompt = (
        f"Conversation Memory:\n{context}\n\n"
        f"User Prompt:\n{prompt}\n\n"
        "Instructions:\n"
        "1. Use the entire conversation memory to recall facts, names, past questions, and previous answers.\n"
        "2. Always maintain consistency with the memory provided.\n"
        "3. If the user asks about something already in memory, use that instead of guessing.\n"
        "4. First, answer the user's question thoroughly.\n"
        "5. Then, on a new line, provide a 25-word summary of this Q&A, prefixed with 'SUMMARY:'.\n"
        "6. Ensure the summary captures key details from both the user's request and your answer."
        )
        response_obj = model.invoke(full_prompt)
        output = response_obj.content

        # Check for API key error
        if "API key not valid" in output or "Please pass a valid API key" in output:
            return {"error": "API key not valid. Please check your Gemini API key."}

        # Split answer and summary
        lines = output.splitlines()
        answer_lines = []
        context_summary = ""
        for line in lines:
            if line.strip().startswith("SUMMARY:"):
                context_summary = line.strip().replace("SUMMARY:", "").strip()
            else:
                answer_lines.append(line)
        answer = "\n".join(answer_lines).strip()

        if not answer or not context_summary:
            return {"error": "API ERROR From Server"}

        return {
            "answer": answer,
            "context_summary": context_summary
        }
    except Exception:
        return {"error": "API ERROR From Server"}
    
# -------------------------------
# Essay endpoint
# -------------------------------
@app.get("/essay")
async def essay(topic: str, length: int = 100):
    try:
        prompt = ChatPromptTemplate.from_template(
    "Write an engaging and informative essay about {topic} in approximately {length} words. "
    "Use clear, simple language so that readers of all ages can enjoy and understand it. "
    "Organize the essay with a brief introduction, a well-structured body, and a thoughtful conclusion. "
    "Make the content interesting and easy to read."
)
        # When you do chain = prompt | model, you create a LangChain "Runnable" chain.
        chain = prompt | model

        # Both the Gemini model (ChatGoogleGenerativeAI) and the chain object support the .invoke() method.
        # This method is used to send input to the model (or chain) and get the output.
        response = chain.invoke({"topic": topic, "length": length})

        return {"topic": topic, "length": length, "essay": response.content}
    except Exception:
        return {"topic": topic, "length": length, "essay": "API ERROR From Server"}

# -------------------------------
# Poem endpoint
# -------------------------------
@app.get("/poem")
async def poem(topic: str, length: int = 30):
    try:
        prompt = ChatPromptTemplate.from_template(
    "Write a creative and heartwarming poem about {topic} in approximately {length} words. "
    "Use simple, relatable language and imagery that resonates with Indian culture and everyday life. "
    "Ensure the poem has a pleasant rhyme scheme and is enjoyable to read for all ages. "
    "Make the poem emotionally engaging and easy to understand."
)
        chain = prompt | model
        response = chain.invoke({"topic": topic, "length": length})
        return {"topic": topic, "length": length, "poem": response.content}
    except Exception:
        return {"topic": topic, "length": length, "poem": "API ERROR From Server"}
    
# -------------------------------
# IMAGE GENERATION ENDPOINT
# -------------------------------
@app.get("/generate-image")
async def generate_image(prompt: str, num_images: int = 2):
    try:
        gemini_request = (
            f"Generate {num_images} distinct image generation prompts for Pollinations AI based on: '{prompt}'. "
            "Return them as a numbered list."
        )
        gemini_response = model.invoke(gemini_request).content

        # Check for API key error in Gemini response
        if "API key not valid" in gemini_response or "Please pass a valid API key" in gemini_response:
            return {"error": "API key not valid. Please check your Gemini API key."}

        # Create the list of the refined prompts we got from the gemini
        prompts = []
        for line in gemini_response.splitlines():
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                prompt_text = line.split('.', 1)[-1].strip() if '.' in line else line.lstrip('-').strip()
                if prompt_text:
                    prompts.append(prompt_text)
            elif line:
                prompts.append(line)
        prompts = prompts[:num_images]

        if not prompts or any([p.lower().startswith("error") for p in prompts]):
            return {"error": "API ERROR From Server"}

        images = []
        for refined_prompt in prompts:
            image_url = f"https://image.pollinations.ai/prompt/{refined_prompt}?nologo=true"
            images.append({"prompt": refined_prompt, "image_url": image_url})

        return {"original_prompt": prompt, "images": images}
    except Exception:
        return {"error": "API ERROR From Server"}


# -------------------------------
# Run server
# -------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
