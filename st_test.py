import streamlit as st
from audio_recorder_streamlit import audio_recorder
from audiorecorder import audiorecorder

if "key" not in st.session_state:
    st.session_state.key = "55"

audio_bytes = audio_recorder("", key="1", )
if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")

audio_bytes2 = audio_recorder(key="2")
if audio_bytes2:
    st.audio(audio_bytes2, format="audio/wav")


st.title("Audio Recorder")

c1, c2, c3 = st.columns([1, 2, 3])

with c1:
    audio = audiorecorder("🎙️", "🟥", "pause", )

with c2:
    audio2 = audiorecorder("", "", show_visualizer=False, key=st.session_state.key)

if audio2:
    print(len(audio2))

with c3:
    audio2 = audiorecorder("", "" , show_visualizer=False, key="511")

def update_a():
    st.session_state.key += "1"

st.button("reset", on_click=update_a)