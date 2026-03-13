import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.google import Gemini
import os

# En lugar de pedir al usuario, lee de secrets
gemini_api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("❌ API Key no configurada")
    st.stop()
