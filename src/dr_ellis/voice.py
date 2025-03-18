import os

import torch
import whisper
from TTS.api import TTS

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
model = whisper.load_model("turbo")


def convert_text_to_speech(text: str):
    speaker = "Wulf Carlevaro"
    language = "ru"
    file_path = "out_voice.wav"

    tts.tts_to_file(
        text=text, speaker=speaker, language=language, file_path=file_path
    )
    os.system(
        f"ffmpeg -i {file_path} "
        f"-ar 16000 -ac 1 -c:a libopus "
        f"{os.path.splitext(file_path)[0]}.ogg -y"
    )


def convert_speech_to_text(input_file: str):
    output_file = f"{os.path.splitext(input_file)[0]}.wav"
    os.system(f"ffmpeg -i {input_file} {output_file} -y")
    result = model.transcribe(output_file)
    return result["text"]
