import asyncio
import base64
import re
import uuid
from typing import Any, Dict, Optional
import google.auth
import google.auth.transport.requests
import requests
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig
from google.cloud import storage
from google.adk.tools import ToolContext

PROJECT_ID = "qwiklabs-gcp-03-fde3effbf431"
BUCKET_NAME = "liftmetrics-media-fde3effbf431"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"
VIDEO_MODEL = "gemini-omni-flash-preview"

_genai_client: Optional[genai.Client] = None
_storage_client: Optional[storage.Client] = None


def get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    return _genai_client


def get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


def _slugify(text: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[-\s]+", "-", clean)


async def generate_exercise_form_image(
    exercise_name: str,
    focus_cue: str = "",
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """Generate an anatomical posture and form guide diagram for an exercise, saving as an artifact and uploading to public Cloud Storage.

    Args:
        exercise_name: Name of the exercise (e.g. 'Barbell Back Squat', 'Romanian Deadlift').
        focus_cue: Specific biomechanics cue to emphasize (e.g. 'spine neutral and bar over midfoot').
        tool_context: ToolContext injected by the agent framework for artifact persistence.

    Returns:
        Dictionary containing status, exercise_name, public image_url, and description.
    """
    try:
        client = get_genai_client()
        prompt = (
            f"A clean, minimalist fitness instructional infographic and anatomical diagram illustrating proper form for {exercise_name}. "
            f"Athletic silhouette showing joint angles and bar path trajectory. "
            f"Focus on key posture cue: {focus_cue if focus_cue else 'neutral spine, proper joint alignment, and balanced base'}. "
            f"Modern vector fitness illustration, high contrast, neutral white background, professional coaching graphic."
        )

        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )

        image_bytes = None
        for candidate in response.candidates:
            if not candidate.content or not candidate.content.parts:
                continue
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    break
            if image_bytes:
                break

        if not image_bytes:
            return {
                "status": "error",
                "message": f"Model generated a response but no image bytes were returned for '{exercise_name}'.",
            }

        slug = _slugify(exercise_name)

        # 1. Save as ADK artifact so it appears in Playground's Artifacts panel
        if tool_context is not None:
            try:
                artifact_part = types.Part(
                    inline_data=types.Blob(mime_type="image/png", data=image_bytes)
                )
                await tool_context.save_artifact(f"{slug}.png", artifact_part)
            except Exception as e:
                # Non-fatal if running outside of artifact-enabled context
                pass

        # 2. Upload image to public Cloud Storage bucket
        storage_client = get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_id = f"{slug}-{uuid.uuid4().hex[:8]}.png"
        blob_path = f"form_guides/{blob_id}"
        blob = bucket.blob(blob_path)

        blob.upload_from_string(image_bytes, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"

        return {
            "status": "success",
            "exercise_name": exercise_name,
            "image_url": public_url,
            "cue_highlighted": focus_cue,
            "message": f"Successfully generated form guide diagram for {exercise_name}.",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate form image: {str(e)}",
        }


async def generate_exercise_motion_video(
    exercise_name: str,
    focus_cue: str = "",
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """Generate a short coaching video clip demonstrating proper exercise movement and cadence using Google's Omni model (gemini-omni-flash-preview).

    Args:
        exercise_name: Name of the exercise (e.g. 'Barbell Back Squat', 'Romanian Deadlift').
        focus_cue: Motion cue to emphasize (e.g. 'controlled eccentric, explosive drive, neutral spine').
        tool_context: ToolContext injected by the agent framework for artifact persistence.

    Returns:
        Dictionary containing status, exercise_name, public video_url, and description.
    """
    try:
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        await asyncio.to_thread(creds.refresh, auth_req)

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        prompt = (
            f"A realistic fitness video clip demonstrating {exercise_name} with flawless biomechanics. "
            f"Athletic person performing the lift with controlled tempo. "
            f"Key coaching focus: {focus_cue if focus_cue else 'proper joint alignment, bar path, and steady cadence'}. "
            f"Gym setting, high definition, side-angle view showing full range of motion."
        )

        payload = {
            "model": VIDEO_MODEL,
            "background": True,
            "input": [{"type": "text", "text": prompt}],
            "response_format": [{"type": "video", "aspect_ratio": "16:9", "duration": "4s"}],
        }

        url = f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/global/interactions"
        resp = await asyncio.to_thread(requests.post, url, headers=headers, json=payload, timeout=30)

        if resp.status_code != 200:
            return {
                "status": "error",
                "message": f"Failed to submit video generation interaction: HTTP {resp.status_code} - {resp.text}",
            }

        res_json = resp.json()
        interaction_id = res_json.get("id")
        if not interaction_id:
            return {
                "status": "error",
                "message": f"No interaction ID returned from video model: {res_json}",
            }

        poll_url = f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/global/interactions/{interaction_id}"

        video_bytes = None
        for _ in range(30):
            await asyncio.sleep(4)
            get_resp = await asyncio.to_thread(requests.get, poll_url, headers=headers, timeout=20)
            if get_resp.status_code != 200:
                continue
            data = get_resp.json()
            status = data.get("status")
            if status == "completed":
                for step in data.get("steps", []):
                    for c in step.get("content", []):
                        if c.get("type") == "video" and "data" in c:
                            video_bytes = base64.b64decode(c["data"])
                            break
                    if video_bytes:
                        break
                break
            elif status == "failed":
                return {
                    "status": "error",
                    "message": f"Video generation interaction failed: {data.get('error', data)}",
                }

        if not video_bytes:
            return {
                "status": "error",
                "message": f"Timed out or no video bytes returned for '{exercise_name}'.",
            }

        slug = _slugify(exercise_name)

        # 1. Save as ADK artifact so it appears in Playground's Artifacts panel
        if tool_context is not None:
            try:
                artifact_part = types.Part(
                    inline_data=types.Blob(mime_type="video/mp4", data=video_bytes)
                )
                await tool_context.save_artifact(f"{slug}.mp4", artifact_part)
            except Exception:
                pass

        # 2. Upload video to public Cloud Storage bucket
        storage_client = get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_id = f"{slug}-{uuid.uuid4().hex[:8]}.mp4"
        blob_path = f"form_videos/{blob_id}"
        blob = bucket.blob(blob_path)

        await asyncio.to_thread(blob.upload_from_string, video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"

        return {
            "status": "success",
            "exercise_name": exercise_name,
            "video_url": public_url,
            "cue_highlighted": focus_cue,
            "message": f"Successfully generated video demonstration for {exercise_name} using Omni.",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate motion video: {str(e)}",
        }

