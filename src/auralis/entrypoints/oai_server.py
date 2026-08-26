import argparse
import base64
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

from auralis.core.tts import TTS
from auralis.common.definitions.openai import VoiceChatCompletionRequest, AudioSpeechGenerationRequest

# Global TTS engine instance
tts_engine: Optional[TTS] = None

logger_str_to_logging = {
    'info': logging.INFO,
    'warn': logging.WARNING,
    'err': logging.ERROR
}

def start_tts_engine(args: argparse.Namespace, logging_level: int):
    global tts_engine
    tts_engine = (TTS(
        vllm_logging_level=logging_level
    ).from_pretrained(
        args.model,
        gpt_model=args.gpt_model,
        max_concurrency=args.max_concurrency
    ))

@asynccontextmanager
async def lifecycle_manager(app: FastAPI):
    global tts_engine
    if tts_engine is None:
        args = argparse.Namespace(
            model='/app/models/xttsv2',
            gpt_model='/app/models/xtts2-gpt',
            max_concurrency=4,
            vllm_logging_level='warn'
        )
        logging_level = logger_str_to_logging.get(args.vllm_logging_level, logging.WARNING)
        start_tts_engine(args, logging_level)
    yield
    if tts_engine is not None:
        await tts_engine.shutdown()

app = FastAPI(lifespan=lifecycle_manager)

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "xttsv2",
                "object": "model",
                "created": 1700000000,
                "owned_by": "astramind"
            },
            {
                "id": "tts-1",
                "object": "model",
                "created": 1700000000,
                "owned_by": "openai"
            },
            {
                "id": "tts-1-hd",
                "object": "model",
                "created": 1700000000,
                "owned_by": "openai"
            }
        ]
    }

@app.get("/v1/audio/voices")
async def list_voices():
    voices_dir = "/app/voices"
    voices = []
    if os.path.exists(voices_dir):
        for f in os.listdir(voices_dir):
            if f.endswith(".wav") or f.endswith(".mp3"):
                vname = os.path.splitext(f)[0]
                voices.append({"id": vname, "name": vname})
    if not voices:
        voices = [{"id": "markus", "name": "markus"}]
    return {"voices": voices}

@app.post("/v1/audio/speech")
async def generate_audio(request: AudioSpeechGenerationRequest):
    if tts_engine is None:
        raise HTTPException(status_code=500, detail="TTS engine not initialized")

    try:
        tts_request = request.to_tts_request()
        output = await tts_engine.generate_speech_async(tts_request)
        if request.speed != 1.0:
            output = output.change_speed(request.speed)
        
        format_name = request.response_format.lower()
        audio_bytes = output.to_bytes(format_name)
        media_type = "audio/wav" if format_name == "wav" else f"audio/{format_name}"

        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return Response(content=audio_bytes, media_type=media_type)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error generating audio: {str(e)}"})

@app.post("/v1/chat/completions")
async def chat_completions(request: VoiceChatCompletionRequest, authorization: Optional[str] = Header(None)):
    if tts_engine is None:
        raise HTTPException(status_code=500, detail="TTS engine not initialized")

    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse(
            status_code=400,
            content={"error": "Authorization header with Bearer token is required"}
        )
    try:
        openai_api_key = authorization[len("Bearer "):]
        modalities = request.modalities
        num_of_token_to_vocalize = request.vocalize_at_every_n_words

        tts_request = request.to_tts_request(text='')
        openai_request_data = request.to_openai_request()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }

        request_id = uuid.uuid4().hex

        valid_modalities = ['text', 'audio']
        if not all(m in valid_modalities for m in modalities):
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid modalities. Must be one or more of {valid_modalities}"}
            )

        async def stream_generator():
            accumulated_content = ""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(request.openai_api_url, json=openai_request_data, headers=headers) as resp:
                        if resp.status != 200:
                            error_response = await resp.text()
                            raise HTTPException(status_code=resp.status, detail=error_response)

                        async for line in resp.content:
                            if not line:
                                continue

                            line = line.decode("utf-8").strip()
                            if not line.startswith("data:"):
                                continue

                            data_str = line[5:].strip()
                            if data_str == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")

                                if content:
                                    accumulated_content += content
                                    if 'text' in modalities:
                                        yield f"data: {json.dumps(data)}\n\n"

                                    if len(accumulated_content.split()) >= num_of_token_to_vocalize:
                                        if 'audio' in modalities:
                                            tts_request.text = accumulated_content
                                            tts_request.infer_language()
                                            audio_output = await tts_engine.generate_speech_async(tts_request)
                                            audio_base64 = base64.b64encode(audio_output.to_bytes()).decode("utf-8")
                                            yield f"data: {json.dumps({'id': request_id, 'object': 'audio.chunk', 'data': audio_base64})}\n\n"

                                        accumulated_content = ""
                                elif 'text' in modalities:
                                    yield f"data: {json.dumps(data)}\n\n"

                            except json.JSONDecodeError:
                                continue

                if accumulated_content and 'audio' in modalities:
                    tts_request.text = accumulated_content
                    tts_request.infer_language()
                    audio_output = await tts_engine.generate_speech_async(tts_request)
                    audio_base64 = base64.b64encode(audio_output.to_bytes()).decode("utf-8")
                    yield f"data: {json.dumps({'id': request_id, 'object': 'audio.chunk', 'data': audio_base64})}\n\n"

                if 'text' in modalities:
                    yield f"data: {json.dumps({'id': request_id, 'object': 'chat.completion.chunk', 'choices': [{'delta': {}, 'index': 0, 'finish_reason': 'stop'}]})}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error in chat completions: {str(e)}"})

def main():
    parser = argparse.ArgumentParser(description="Auralis TTS FastAPI Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8502, help="Port to run the server on")
    parser.add_argument("--model", type=str, default='/app/models/xttsv2', help="The base model to run")
    parser.add_argument("--gpt_model", type=str, default='/app/models/xtts2-gpt', help="The gpt model to load alongside the base model, if present")
    parser.add_argument("--max_concurrency", type=int, default=4, help="The concurrency value that is used in the TTS Engine")
    parser.add_argument("--vllm_logging_level", type=str, default='warn', help="The vllm logging level")

    args = parser.parse_args()

    logging_level = logger_str_to_logging.get(args.vllm_logging_level, logging.WARNING)
    start_tts_engine(args, logging_level)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
    )

if __name__ == "__main__":
    main()
