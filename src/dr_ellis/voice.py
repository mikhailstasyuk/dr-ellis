import os

import torch
from TTS.api import TTS

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)


def convert_text_to_speech(
    text: str, speaker: str, language: str, file_path: str
):
    tts.tts_to_file(
        text=text, speaker=speaker, language=language, file_path=file_path
    )


def convert_wav_to_ogg(wav_file: str, ogg_file: str):
    os.system(f"ffmpeg -i {wav_file} {ogg_file} -y")


def create_audio(text: str):
    convert_text_to_speech(text, "Wulf Carlevaro", "ru", "output.wav")
    convert_wav_to_ogg("output.wav", "output.ogg")
