"""
TokenLens — Gemini API Client
===============================
Wrapper around google-generativeai SDK with secret management,
structured logging, and error handling.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

import google.genai as genai

logger = logging.getLogger("tokenlens.gemini")

# Regex to mask API keys in logs
_KEY_MASK_RE = re.compile(r"(AIza[A-Za-z0-9_-]{35})")


def _mask_key(text: str) -> str:
    """Mask API keys in text to prevent log leakage."""
    return _KEY_MASK_RE.sub("AIza***MASKED***", text)


class GeminiClient:
    """
    Manages Gemini API configuration, model instantiation, and generation.
    Loads the API key from env var or Google Secret Manager.
    """

    def __init__(self) -> None:
        self._api_key: Optional[str] = None
        self._configured = False
        self._configure()

    def _configure(self) -> None:
        """Load API key and configure the SDK."""
        self._api_key = os.environ.get("GEMINI_API_KEY")

        if not self._api_key:
            self._api_key = self._fetch_from_secret_manager()

        if not self._api_key:
            logger.warning(
                "GEMINI_API_KEY not found. Set the environment variable or "
                "configure Google Secret Manager."
            )
            return

        genai.configure(api_key=self._api_key)
        self._configured = True
        logger.info("Gemini API configured (key=%s)", _mask_key(self._api_key[:10] + "..."))

    @staticmethod
    def _fetch_from_secret_manager() -> Optional[str]:
        """Attempt to fetch API key from Google Cloud Secret Manager."""
        try:
            from google.cloud import secretmanager

            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                return None

            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{project_id}/secrets/GEMINI_API_KEY/versions/latest"
            response = client.access_secret_version(request={"name": secret_name})
            key = response.payload.data.decode("UTF-8").strip()
            logger.info("Fetched API key from Secret Manager")
            return key
        except Exception as e:
            logger.debug("Secret Manager not available: %s", e)
            return None

    async def generate(self, prompt: str, model_name: str) -> str:
        """
        Generate a response using the specified Gemini model.

        Args:
            prompt: The prompt to send.
            model_name: Gemini model identifier.

        Returns:
            The generated text response.

        Raises:
            RuntimeError: If the API is not configured.
            Exception: Propagated from the Gemini SDK.
        """
        if not self._configured:
            raise RuntimeError(
                "Gemini API is not configured. Set GEMINI_API_KEY env var."
            )

        try:
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)

            if response and response.text:
                logger.info(
                    "Generated response: model=%s, length=%d chars",
                    model_name, len(response.text),
                )
                return response.text

            logger.warning("Empty response from Gemini model=%s", model_name)
            return "[No response generated]"

        except Exception as e:
            logger.error("Gemini API error: model=%s, error=%s", model_name, _mask_key(str(e)))
            raise

    @property
    def is_configured(self) -> bool:
        """Check if the Gemini client is properly configured."""
        return self._configured
