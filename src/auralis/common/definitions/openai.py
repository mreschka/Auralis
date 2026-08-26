import base64
import os
from dataclasses import fields

from openai import OpenAI
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any, Literal, Union
from auralis.common.definitions.requests import TTSRequest


class ChatCompletionMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

tts_defaults = {field.name: field.default for field in fields(TTSRequest)}

def resolve_voice_file(item: str) -> str:
    voice_dir = "/app/voices"
    candidates = [
        item,
        f"{item}.wav",
        f"{item}.mp3",
        os.path.join(voice_dir, item),
        os.path.join(voice_dir, f"{item}.wav"),
        os.path.join(voice_dir, f"{item}.mp3"),
    ]
    for cand in candidates:
        if os.path.exists(cand) and os.path.isfile(cand):
            with open(cand, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    # Try as base64
    try:
        base64.b64decode(item)
        return item
    except Exception:
        # Fallback to markus.wav if available
        fallback = os.path.join(voice_dir, "markus.wav")
        if os.path.exists(fallback):
            with open(fallback, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        raise ValueError(f"Voice '{item}' not found in {voice_dir} and is not valid base64")

class VoiceChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessage]
    speaker_files: Union[str, List[str]] = Field(..., description="List of base64-encoded audio files or voice names")
    modalities: List[Literal["text", "audio"]] = Field(
        default=["text", "audio"],
        description="Output modalities to return"
    )
    openai_api_url: Optional[str] = Field(
        default=None,
        description="Custom OpenAI API endpoint to make the LLM request to"
    )
    vocalize_at_every_n_words: int = Field(
        default=100,
        ge=1,
        description="Number of words after which to generate audio"
    )
    stream: bool = Field(default=True)

    enhance_speech: bool = Field(default=tts_defaults['enhance_speech'])
    language: str = Field(default='de')
    max_ref_length: int = Field(default=tts_defaults['max_ref_length'])
    gpt_cond_len: int = Field(default=tts_defaults['gpt_cond_len'])
    gpt_cond_chunk_len: int = Field(default=tts_defaults['gpt_cond_chunk_len'])
    temperature: float = Field(default=tts_defaults['temperature'])
    top_p: float = Field(default=tts_defaults['top_p'])
    top_k: int = Field(default=tts_defaults['top_k'])
    repetition_penalty: float = Field(default=tts_defaults['repetition_penalty'])
    length_penalty: float = Field(default=tts_defaults['length_penalty'])
    do_sample: bool = Field(default=tts_defaults['do_sample'])

    @field_validator('openai_api_url')
    def validate_oai_url(cls, v):
        if v is None:
            raise ValueError("You should always give a url for the text generation")
        return v

    @field_validator('stream')
    def validate_stream(cls, v):
        if not v:
            raise ValueError('Streaming should be enabled! For non-streaming conversion use the audio endpoint')
        return v

    @field_validator('speaker_files', mode='before')
    def validate_speaker_files(cls, v):
        if isinstance(v, str):
            v = [v]
        if not v:
            v = ["markus"]
        return [resolve_voice_file(f) for f in v]

    @field_validator('modalities')
    def validate_modalities(cls, v):
        valid_modalities = ["text", "audio"]
        if not all(m in valid_modalities for m in v):
            raise ValueError(f"Invalid modalities. Must be one or more of {valid_modalities}")
        return v

    def to_tts_request(self, text: str = "") -> TTSRequest:
        speaker_data_list = [base64.b64decode(f) for f in self.speaker_files]
        return TTSRequest(
            text=text,
            stream=False,
            speaker_files=speaker_data_list,
            enhance_speech=self.enhance_speech,
            language=self.language,
            max_ref_length=self.max_ref_length,
            gpt_cond_len=self.gpt_cond_len,
            gpt_cond_chunk_len=self.gpt_cond_chunk_len,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            repetition_penalty=self.repetition_penalty,
            length_penalty=self.length_penalty,
            do_sample=self.do_sample
        )

    def to_openai_request(self) -> Dict[str, Any]:
        oai_dict = {
            k: v for k, v in self.model_dump().items()
            if k not in ["speaker_files", "openai_api_url", "vocalize_at_every_n_words", 'modalities'] and
               not k in tts_defaults.keys()
        }
        oai_dict.update({"stream": True})
        return oai_dict


class AudioSpeechGenerationRequest(BaseModel):
    input: str = Field(..., description="The textual input to convert")
    model: str = Field(default="xttsv2", description="The model to use for conversion")
    voice: Union[str, List[str]] = Field(default="markus", description="Voice name from /app/voices or base64-encoded audio file(s)")
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = Field(
        default='wav', description="Audio response format"
    )
    speed: float = Field(default=1.0, description="Speech speed")

    enhance_speech: bool = Field(default=tts_defaults['enhance_speech'])
    normalize: Optional[bool] = Field(default=None, description="Enable or disable text normalization/phonetization for this request")
    language: str = Field(default='de')
    max_ref_length: int = Field(default=tts_defaults['max_ref_length'])
    gpt_cond_len: int = Field(default=tts_defaults['gpt_cond_len'])
    gpt_cond_chunk_len: int = Field(default=tts_defaults['gpt_cond_chunk_len'])
    temperature: float = Field(default=tts_defaults['temperature'])
    top_p: float = Field(default=tts_defaults['top_p'])
    top_k: int = Field(default=tts_defaults['top_k'])
    repetition_penalty: float = Field(default=tts_defaults['repetition_penalty'])
    length_penalty: float = Field(default=tts_defaults['length_penalty'])
    do_sample: bool = Field(default=tts_defaults['do_sample'])

    @field_validator('voice', mode='before')
    def validate_voice(cls, v):
        if isinstance(v, str):
            v = [v]
        if not v:
            v = ["markus"]
        return [resolve_voice_file(f) for f in v]

    def to_tts_request(self) -> TTSRequest:
        speaker_data_list = [base64.b64decode(f) for f in self.voice]
        return TTSRequest(
            text=self.input,
            stream=False,
            speaker_files=speaker_data_list,
            enhance_speech=self.enhance_speech,
            language=self.language,
            max_ref_length=self.max_ref_length,
            gpt_cond_len=self.gpt_cond_len,
            gpt_cond_chunk_len=self.gpt_cond_chunk_len,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            repetition_penalty=self.repetition_penalty,
            length_penalty=self.length_penalty,
            do_sample=self.do_sample
        )
