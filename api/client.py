import requests
import streamlit as st
import os
import glob

# ================================
# Storage Functions
# ================================

# This is used to save the file to the specified directory
def save_to_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

# This is use to load the data from the file
def load_from_file(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    return ""

IMAGES_FILE = "../storage/images.txt"
IMAGES_DIR = "../storage/images"


def save_images_info(prompt, images):
    # Save prompt and local image paths to images.txt
    with open(IMAGES_FILE, "w", encoding="utf-8") as f:
        f.write(f"{prompt}\n")
        for idx in range(1, len(images)+1):
            local_path = os.path.join(IMAGES_DIR, f"{idx}.jpg")
            f.write(f"{idx}: {local_path}\n")

    # Save each image file to storage/images/1.jpg, 2.jpg, 3.jpg
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

    # This loops over the images list, giving you both the index (idx) and the image dictionary (img).
    # The 1 means indexing starts at 1 (not 0), so the first image will be saved as 1.jpg, the second as 2.jpg, etc.
    for idx, img in enumerate(images, 1):
        img_url = img['image_url']
        img_path = os.path.join(IMAGES_DIR, f"{idx}.jpg")
        try:
            response = requests.get(img_url)
            if response.status_code == 200:
                with open(img_path, "wb") as img_file:
                    img_file.write(response.content)
        except Exception as e:
            print(f"Error downloading image {idx}: {e}")

def load_images_info():
    if os.path.exists(IMAGES_FILE):
        with open(IMAGES_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                prompt = lines[0].strip()
                image_paths = [line.split(": ", 1)[1].strip() for line in lines[1:] if ": " in line]
                return prompt, image_paths
    return "", []




CONV_DIR = "../storage/conversations"

# This function gets the next available conversation ID 
def get_next_conversation_id():
    if not os.path.exists(CONV_DIR):
        os.makedirs(CONV_DIR)
    files = glob.glob(os.path.join(CONV_DIR, "*.txt"))
    ids = [int(os.path.splitext(os.path.basename(f))[0]) for f in files if os.path.basename(f).split('.')[0].isdigit()]
    return max(ids, default=0) + 1

# This function saves the conversation exchanges to a file
def save_conversation(conv_id, exchanges):
    if not os.path.exists(CONV_DIR):
        os.makedirs(CONV_DIR)
    with open(os.path.join(CONV_DIR, f"{conv_id}.txt"), "w", encoding="utf-8") as f:
        for ex in exchanges:
            f.write(f"PROMPT: {ex['prompt']}\n")
            f.write(f"ANSWER: {ex['answer']}\n")
            f.write(f"CONTEXT: {ex['context']}\n\n")

# This function loads all the conversation we did when we select the particular chat
def load_conversation(conv_id):
    path = os.path.join(CONV_DIR, f"{conv_id}.txt")
    exchanges = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            block = {}
            for line in f:
                if line.startswith("PROMPT:"):
                    block['prompt'] = line[len("PROMPT:"):].strip()
                elif line.startswith("ANSWER:"):
                    block['answer'] = line[len("ANSWER:"):].strip()
                elif line.startswith("CONTEXT:"):
                    block['context'] = line[len("CONTEXT:"):].strip()
                elif line.strip() == "":
                    if block:
                        exchanges.append(block)
                        block = {}
            if block:
                exchanges.append(block)
    return exchanges

# Delete the conversation 
def delete_conversation(conv_id):
    path = os.path.join(CONV_DIR, f"{conv_id}.txt")
    if os.path.exists(path):
        os.remove(path)

# ================================
# API Call Functions
# ================================
BASE_URL = "http://localhost:8000"

# def get_gemini_chat(user_input):
#     response = requests.post(f"{BASE_URL}/gemini/invoke", json={'input': user_input})
#     return response.json()['output']['content']

def get_gemini_companion_api(user_input, context):
    try:
        response = requests.post(
            f"{BASE_URL}/companion",
            params={"prompt": user_input, "context": context}
        )
        data = response.json()
        if "error" in data:
            return None, None, f"Error: {data['error']}"
        return data["answer"], data["context_summary"], None
    except Exception as e:
        return None, None, f"Error: {str(e)}"

def generate_text(task_type, topic, length):
    try:
        if task_type.lower() == "essay":
            response = requests.get(f"{BASE_URL}/essay", params={"topic": topic, "length": length})
            if response.status_code == 200:
                return response.json().get("essay", "Can't got the essay object")
            else:
                return "Bad request"
        elif task_type.lower() == "poem":
            response = requests.get(f"{BASE_URL}/poem", params={"topic": topic, "length": length})
            if response.status_code == 200:
                return response.json().get("poem", "Can't got the poem object")
            else:
                return "Bad request"
        else:
            return "Bad request"
    except Exception:
        return "API ERROR From Server"

def generate_image(prompt, num_images):
    response = requests.get(f"{BASE_URL}/generate-image", params={"prompt": prompt, "num_images": num_images})
    return response.json()


# ================================
# Streamlit UI
# ================================
st.set_page_config(page_title="Creative Studio", page_icon="✨")
st.title("✨ Creative Studio ✨")
st.caption("Explore essays, poems, conversations, images, and audio in one place.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Essay", "🎵 Poem", "🤖 Companion", "🖼 Image"])

ESSAY_FILE = "../storage/essay.txt"
POEM_FILE = "../storage/poem.txt"

# -------------------------------
# Essay
# -------------------------------
with tab1:
    topic = st.text_input("Enter a topic for your essay:")
    length = st.slider("Select essay length (words)", 20, 300, 100)

    # Load essay from session_state or file
    if "essay_data" not in st.session_state:
        last_essay_data = load_from_file(ESSAY_FILE)
        st.session_state.essay_data = last_essay_data
    else:
        last_essay_data = st.session_state.essay_data

    if st.button("Generate Essay", key="essay_btn"):
        if topic:
            essay = generate_text("essay", topic, length)
            
            # Handles the ERROR
            if(essay == "Bad request" or essay == "API ERROR From Server" or 
               essay == "Can't got the essay object" or essay =="API ERROR From Server-Client"):
                st.error("Error generating essay.")
                if last_essay_data:
                    parts = last_essay_data.split('\n---\n', 1)
                    if len(parts) == 2:
                        last_topic, last_essay = parts
                        st.subheader(f"Topic: {last_topic}")
                        st.write(last_essay)
            else:
                # Save both topic and essay, separated by a special marker
                save_to_file(ESSAY_FILE, f"{topic}\n---\n{essay}")
                st.session_state.essay_data = f"{topic}\n---\n{essay}"
                st.subheader(f"Topic: {topic}")
                st.write(essay)
    else:
        if last_essay_data:
            parts = last_essay_data.split('\n---\n', 1)
            if len(parts) == 2:
                last_topic, last_essay = parts
                st.subheader(f"Topic: {last_topic}")
                st.write(last_essay)

# -------------------------------
# Poem
# -------------------------------
with tab2:
    topic = st.text_input("Enter a topic for your poem:")
    length = st.slider("Select poem length (words)", 5, 100, 30)
    if "poem_data" not in st.session_state:
        last_poem_data = load_from_file(POEM_FILE)
        st.session_state.poem_data = last_poem_data
    else:
        last_poem_data = st.session_state.poem_data

    if st.button("Generate Poem", key="poem_btn"):
        if topic:
            poem = generate_text("poem", topic, length)
            if(poem == "Bad request" or poem == "API ERROR From Server" or 
               poem == "Can't got the poem object" or poem =="API ERROR From Server-Client"):
                st.error("Error generating poem.")
                if last_poem_data:
                    parts = last_poem_data.split('\n---\n', 1)
                    if len(parts) == 2:
                        last_topic, last_poem = parts
                        st.subheader(f"Topic: {last_topic}")
                        st.write(last_poem)
            else:
                save_to_file(POEM_FILE, f"{topic}\n---\n{poem}")
                st.session_state.poem_data = f"{topic}\n---\n{poem}"
                st.subheader(f"Topic: {topic}")
                st.write(poem)
    else:
        if last_poem_data:
            parts = last_poem_data.split('\n---\n', 1)
            if len(parts) == 2:
                last_topic, last_poem = parts
                st.subheader(f"Topic: {last_topic}")
                st.write(last_poem)

# -------------------------------
# Chatbot
# -------------------------------
with tab3:
    st.subheader("Your AI Companion")

    # Cache conversations in session_state
    if "conv_files" not in st.session_state:
        conv_files = sorted(glob.glob(os.path.join(CONV_DIR, "*.txt")), key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
        st.session_state.conv_files = conv_files
        st.session_state.conv_ids = [int(os.path.splitext(os.path.basename(f))[0]) for f in conv_files]
    # Always define conv_files and conv_ids
    conv_files = st.session_state.conv_files
    conv_ids = st.session_state.conv_ids

    def conversation_name(conv_id):
        # Cache exchanges per conversation
        if f"exchanges_{conv_id}" not in st.session_state:
            exchanges = load_conversation(conv_id)
            st.session_state[f"exchanges_{conv_id}"] = exchanges
        else:
            exchanges = st.session_state[f"exchanges_{conv_id}"]
        if exchanges and exchanges[0].get("prompt"):
            return exchanges[0]["prompt"]
        return "New Conversation"

    # Handle empty conversations gracefully
    if conv_ids:
        selected_conv = st.selectbox(
            "Select Conversation",
            conv_ids,
            format_func=conversation_name
        )
    else:
        selected_conv = None
        st.info("No conversations found. Click 'New Conversation' to start.")

    if st.button("New Conversation"):
        selected_conv = get_next_conversation_id()
        save_conversation(selected_conv, [])
        # Update session_state
        st.session_state.conv_files = sorted(glob.glob(os.path.join(CONV_DIR, "*.txt")), key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
        st.session_state.conv_ids = [int(os.path.splitext(os.path.basename(f))[0]) for f in st.session_state.conv_files]
        st.session_state[f"exchanges_{selected_conv}"] = []
        st.rerun()

    if selected_conv and st.button("Delete Conversation"):
        delete_conversation(selected_conv)
        # Update session_state
        st.session_state.conv_files = sorted(glob.glob(os.path.join(CONV_DIR, "*.txt")), key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
        st.session_state.conv_ids = [int(os.path.splitext(os.path.basename(f))[0]) for f in st.session_state.conv_files]
        if f"exchanges_{selected_conv}" in st.session_state:
            del st.session_state[f"exchanges_{selected_conv}"]
        st.rerun()

    if selected_conv:
        if f"exchanges_{selected_conv}" not in st.session_state:
            exchanges = load_conversation(selected_conv)
            st.session_state[f"exchanges_{selected_conv}"] = exchanges
        else:
            exchanges = st.session_state[f"exchanges_{selected_conv}"]
        for ex in exchanges:
            if 'prompt' in ex:
                st.markdown(f"**You:** {ex['prompt']}")
            if 'answer' in ex:
                st.markdown(f"**Companion:** {ex['answer']}")
        # Use text_area for bigger prompt input
        user_input = st.text_area("Type your message...", key=f"companion_input_{selected_conv}", height=120)
        if st.button("Send", key=f"companion_send_{selected_conv}"):
            if user_input:
                context = " ".join([ex['context'] for ex in exchanges if 'context' in ex])
                answer, context_summary, error = get_gemini_companion_api(user_input, context)
                if error:
                    st.error(error)
                else:
                    exchanges.append({"prompt": user_input, "answer": answer, "context": context_summary})
                    save_conversation(selected_conv, exchanges)
                    st.session_state[f"exchanges_{selected_conv}"] = exchanges
                    st.rerun()

# -------------------------------
# Image
# -------------------------------
with tab4:
    img_prompt = st.text_input("Enter prompt for image generation:")
    num_images = st.slider("Number of images", min_value=1, max_value=5, value=3)
    # Cache image info in session_state
    if "images_info" not in st.session_state:
        last_prompt, last_image_paths = load_images_info()
        st.session_state.images_info = (last_prompt, last_image_paths)
    else:
        last_prompt, last_image_paths = st.session_state.images_info

    if st.button("Generate Image", key="img_btn"):
        if img_prompt:
            result = generate_image(img_prompt, num_images)
            if "error" in result or not result.get("images"):
                st.error("Error generating images.")
                if last_image_paths:
                    st.subheader(f"Prompt: {last_prompt}")
                    cols = st.columns(len(last_image_paths))
                    for idx, img_path in enumerate(last_image_paths, 1):
                        with cols[idx-1]:
                            st.image(img_path, use_container_width=True)
                            st.caption(f"Variation {idx}")
            else:
                images = result["images"]
                save_images_info(img_prompt, images)
                image_paths = [os.path.join(IMAGES_DIR, f"{idx}.jpg") for idx in range(1, num_images+1)]
                st.session_state.images_info = (img_prompt, image_paths)
                st.subheader(f"Prompt: {img_prompt}")
                cols = st.columns(num_images)
                for idx in range(1, num_images+1):
                    img_path = os.path.join(IMAGES_DIR, f"{idx}.jpg")
                    with cols[idx-1]:
                        st.image(img_path, use_container_width=True)
                        st.caption(f"Variation {idx}")
    else:
        if last_image_paths:
            st.subheader(f"Prompt: {last_prompt}")
            cols = st.columns(len(last_image_paths))
            for idx, img_path in enumerate(last_image_paths, 1):
                with cols[idx-1]:
                    st.image(img_path, use_container_width=True)
                    st.caption(f"Variation {idx}")

