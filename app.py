import streamlit as st
import google.generativeai as genai
import requests

st.set_page_config(page_title="World of Bots Beta", layout="wide")

def gerar_voz(texto, voice_id, api_key_eleven):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key_eleven,
        "Content-Type": "application/json"
    }
    data = {
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.content
    return None

if "bot_directory" not in st.session_state:
    st.session_state.bot_directory = [
        {"name": "Darth Vader", "prompt": "Você é Darth Vader. Responda de forma sombria e curta.", "voice_id": "onwK4e9ZLuTAKqD09m5D", "creator": "Sistema", "public": True},
        {"name": "Geralt de Rívia", "prompt": "Você é Geralt de Rívia. Seja sarcástico e pragmático.", "voice_id": "Lcf7W3959nSgUv2FvLCz", "creator": "Sistema", "public": True}
    ]

if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}

with st.sidebar:
    st.title("🛠️ Painel do Criador")
    gemini_key = st.text_input("Gemini API Key", type="password")
    eleven_key = st.text_input("ElevenLabs API Key", type="password")
    st.divider()
    st.subheader("Criar Novo Personagem")
    new_name = st.text_input("Nome do Personagem")
    new_prompt = st.text_area("Personalidade")
    new_voice = st.text_input("ID da Voz (ElevenLabs)")
    if st.button("Salvar Personagem"):
        st.session_state.bot_directory.append({"name": new_name, "prompt": new_prompt, "voice_id": new_voice, "creator": "Você", "public": True})
        st.success("Bot criado!")

st.title("🌌 World of Bots - Versão Beta")
cols = st.columns(3)
for i, bot in enumerate(st.session_state.bot_directory):
    with cols[i % 3]:
        st.info(f"**{bot['name']}**")
        if st.button(f"Conversar com {bot['name']}", key=f"btn_{i}"):
            st.session_state.current_bot = bot

if "current_bot" in st.session_state and gemini_key:
    bot = st.session_state.current_bot
    chat_id = bot["name"]
    if chat_id not in st.session_state.chat_histories:
        st.session_state.chat_histories[chat_id] = []
    st.divider()
    st.subheader(f"Conversando com: {bot['name']}")
    for msg in st.session_state.chat_histories[chat_id]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if prompt := st.chat_input("Diga algo..."):
        st.session_state.chat_histories[chat_id].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=bot["prompt"])
        history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.chat_histories[chat_id]]
        chat = model.start_chat(history=history[:-1])
        response = chat.send_message(prompt)
        texto_ia = response.text
        with st.chat_message("assistant"):
            st.markdown(texto_ia)
            if eleven_key and bot["voice_id"]:
                audio = gerar_voz(texto_ia, bot["voice_id"], eleven_key)
                if audio:
                    st.audio(audio, format="audio/mp3")
        st.session_state.chat_histories[chat_id].append({"role": "assistant", "content": texto_ia})
