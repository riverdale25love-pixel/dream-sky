import streamlit as st
import google.generativeai as genai
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="World of Bots Pro", layout="wide")

# --- FUNÇÕES DE APOIO (API) ---
def clonar_voz(nome, arquivo_audio, api_key):
    """Envia um áudio para a ElevenLabs para criar um novo Voice ID"""
    url = "https://api.elevenlabs.io/v1/voices/add"
    headers = {"xi-api-key": api_key}
    files = {"files": (arquivo_audio.name, arquivo_audio.read(), arquivo_audio.type)}
    data = {"name": f"Voz_{nome}", "description": f"Clonada para {nome}"}
    try:
        response = requests.post(url, headers=headers, data=data, files=files)
        if response.status_code == 200:
            return response.json().get("voice_id")
    except:
        return None
    return None

def gerar_voz(texto, voice_id, api_key):
    """Transforma o texto da resposta em áudio usando o Voice ID"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    data = {
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
    except:
        return None
    return None

# --- GERENCIAMENTO DE ESTADO (MEMÓRIA) ---
if "bot_directory" not in st.session_state:
    st.session_state.bot_directory = []

if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}

# --- BARRA LATERAL: CONFIGURAÇÃO E CRIAÇÃO ---
with st.sidebar:
    st.title("🛠️ Painel de Criação")
    st.info("Insira suas chaves para habilitar a IA e a Voz.")
    gemini_key = st.text_input("Gemini API Key", type="password")
    eleven_key = st.text_input("ElevenLabs API Key", type="password")
    
    st.divider()
    st.subheader("🆕 Criar Novo Personagem")
    new_name = st.text_input("Nome do Personagem")
    new_prompt = st.text_area("Personalidade / Regras do Chat")
    
    # Upload de Imagem
    new_photo = st.file_uploader("🖼️ Foto do Personagem", type=["jpg", "png", "jpeg"])
    
    # Upload de Áudio para Clonagem
    st.markdown("---")
    st.markdown("**🎙️ Clonagem de Voz (Opcional)**")
    voice_file = st.file_uploader("Suba um áudio (mp3/wav) para clonar a voz", type=["mp3", "wav"])
    
    if st.button("🚀 Criar e Salvar Personagem"):
        if not new_name or not new_prompt:
            st.error("Nome e Personalidade são obrigatórios!")
        else:
            v_id = None
            # Tenta clonar a voz se o arquivo e a chave existirem
            if voice_file and eleven_key:
                with st.spinner("Clonando voz na ElevenLabs..."):
                    v_id = clonar_voz(new_name, voice_file, eleven_key)
            
            # Adiciona ao diretório
            st.session_state.bot_directory.append({
                "name": new_name, 
                "prompt": new_prompt, 
                "voice_id": v_id,
                "photo": new_photo.read() if new_photo else None
            })
            st.success(f"O bot '{new_name}' foi criado com sucesso!")

# --- CORPO PRINCIPAL: GALERIA ---
st.title("🌌 World of Bots - Galeria Pro")

if not st.session_state.bot_directory:
    st.write("Ainda não há bots criados. Use a barra lateral para começar!")
else:
    # Exibe os bots em colunas
    cols = st.columns(3)
    for i, bot in enumerate(st.session_state.bot_directory):
        with cols[i % 3]:
            if bot["photo"]:
                st.image(bot["photo"], use_container_width=True)
            else:
                st.image("https://via.placeholder.com/150", caption="Sem Foto")
            
            st.subheader(bot["name"])
            if st.button(f"Conversar com {bot['name']}", key=f"btn_{i}"):
                st.session_state.current_bot = bot

# --- ÁREA DE CHAT ---
if "current_bot" in st.session_state:
    bot = st.session_state.current_bot
    st.divider()
    st.header(f"💬 Conversando com: {bot['name']}")
    
    if not gemini_key:
        st.warning("⚠️ Insira a Gemini API Key na lateral para conversar.")
    else:
        # Inicializa histórico específico deste bot
        if bot['name'] not in st.session_state.chat_histories:
            st.session_state.chat_histories[bot['name']] = []

        # Exibe mensagens anteriores
        for m in st.session_state.chat_histories[bot['name']]:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        # Entrada de texto do usuário
        if p := st.chat_input(f"Falar com {bot['name']}..."):
            # Adiciona mensagem do usuário
            st.session_state.chat_histories[bot['name']].append({"role": "user", "content": p})
            with st.chat_message("user"):
                st.markdown(p)
            
            # Configura e chama o Gemini
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=bot["prompt"])
            
            try:
                response = model.generate_content(p)
                res_text = response.text
                
                with st.chat_message("assistant"):
                    st.markdown(res_text)
                    
                    # Se houver Voice ID e chave da ElevenLabs, gera áudio
                    if eleven_key and bot["voice_id"]:
                        with st.spinner("Gerando voz..."):
                            audio_bytes = gerar_voz(res_text, bot["voice_id"], eleven_key)
                            if audio_bytes:
                                st.audio(audio_bytes)
                
                # Salva no histórico
                st.session_state.chat_histories[bot['name']].append({"role": "assistant", "content": res_text})
            except Exception as e:
                st.error(f"Erro na IA: {e}")
