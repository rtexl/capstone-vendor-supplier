from contextlib import ExitStack, contextmanager, nullcontext
from functools import lru_cache
import hashlib
import logging
import re
from typing import Any, Iterator, Literal

from app.config import Settings, get_settings
from app.services.redaction import redact_pii

logger = logging.getLogger(__name__)

ObservationType = Literal[
    "span",
    "generation",
    "embedding",
    "retriever",
    "evaluator",
    "guardrail",
]

_SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "bank_account_number",
    "password",
    "secret",
    "secret_key",
    "tax_reference",
    "token",
}
_SECRET_VALUE = re.compile(r"(?i)\b(?:bearer\s+)?sk-[a-z0-9._-]{10,}\b")


def mask_trace_data(data: Any, **_: Any) -> Any:
    """Apply a final defensive mask before telemetry leaves the process."""
    if isinstance(data, str):
        return _SECRET_VALUE.sub("[SECRET]", redact_pii(data).text)
    if isinstance(data, dict):
        return {
            str(key): (
                "[REDACTED]"
                if str(key).casefold() in _SENSITIVE_KEYS
                else mask_trace_data(value)
            )
            for key, value in data.items()
        }
    if isinstance(data, (list, tuple)):
        return [mask_trace_data(item) for item in data]
    return data


class _NoopObservation:
    def update(self, **_: Any) -> None:
        return None

    def update_trace(self, **_: Any) -> None:
        return None

    def score_trace(self, **_: Any) -> None:
        return None

    def set_trace_io(self, **_: Any) -> None:
        return None


class _SafeObservation:
    """Keep telemetry update failures from changing application behavior."""

    def __init__(self, observation: Any):
        self.observation = observation

    def update(self, **kwargs: Any) -> None:
        try:
            self.observation.update(**mask_trace_data(kwargs))
        except Exception:  # pragma: no cover - SDK/network-specific failure
            logger.debug("Langfuse observation update failed.", exc_info=True)

    def update_trace(self, **kwargs: Any) -> None:
        try:
            updater = getattr(self.observation, "update_trace", None)
            if updater is not None:
                updater(**mask_trace_data(kwargs))
        except Exception:  # pragma: no cover - SDK/network-specific failure
            logger.debug("Langfuse trace update failed.", exc_info=True)

    def score_trace(self, **kwargs: Any) -> None:
        try:
            scorer = getattr(self.observation, "score_trace", None)
            if scorer is not None:
                scorer(**mask_trace_data(kwargs))
        except Exception:  # pragma: no cover - SDK/network-specific failure
            logger.debug("Langfuse trace scoring failed.", exc_info=True)

    def set_trace_io(self, *, input_data: Any = None, output_data: Any = None) -> None:
        try:
            self.observation.set_trace_io(
                input=mask_trace_data(input_data),
                output=mask_trace_data(output_data),
            )
        except Exception:  # pragma: no cover - SDK/network-specific failure
            logger.debug("Langfuse trace I/O update failed.", exc_info=True)


def telemetry_subject_id(value: Any) -> str:
    """Return a stable, non-reversible label suitable for telemetry grouping."""
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]
    return f"supplier-{digest}"


class LangfuseTracer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.capture_content = settings.langfuse_capture_content
        self.client: Any | None = None
        self._propagate_attributes: Any | None = None

        secret_key = (
            settings.langfuse_secret_key.get_secret_value()
            if settings.langfuse_secret_key
            else ""
        )
        if not settings.langfuse_enabled or not settings.langfuse_public_key or not secret_key:
            return

        try:
            from langfuse import Langfuse, propagate_attributes

            self.client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=secret_key,
                base_url=settings.langfuse_base_url,
                environment=settings.app_env,
                release=settings.langfuse_release or None,
                tracing_enabled=True,
                mask=mask_trace_data,
            )
            self._propagate_attributes = propagate_attributes
        except Exception:  # pragma: no cover - SDK initialization failure
            logger.warning(
                "Langfuse tracing could not be initialized; continuing without tracing.",
                exc_info=True,
            )

    @property
    def propagate_attributes(self) -> Any | None:
        """Expose the propagation hook used by the original tracing API."""
        return self._propagate_attributes

    @propagate_attributes.setter
    def propagate_attributes(self, value: Any | None) -> None:
        self._propagate_attributes = value

    def input_payload(self, metadata: dict[str, Any], content: Any = None) -> dict[str, Any]:
        if not self.capture_content:
            return mask_trace_data(metadata)
        return mask_trace_data({"metadata": metadata, "content": content})

    def output_payload(self, metadata: dict[str, Any], content: Any = None) -> dict[str, Any]:
        if not self.capture_content:
            return mask_trace_data(metadata)
        return mask_trace_data({"metadata": metadata, "content": content})

    def model_name(self, provider_model: str) -> str:
        """Return the canonical model name while retaining the provider model in metadata."""
        if self.settings.ai_provider == "openrouter" and "/" in provider_model:
            return provider_model.split("/", 1)[1]
        return provider_model

    @contextmanager
    def trace(
        self,
        *,
        name: str,
        input_data: Any,
        metadata: dict[str, Any] | None = None,
        subject_id: str | None = None,
        session_id: str | None = None,
        tags: list[str] | None = None,
    ) -> Iterator[_SafeObservation | _NoopObservation]:
        """Compatibility wrapper for callers using the original parent-trace API."""
        if self.client is None:
            yield _NoopObservation()
            return

        safe_metadata = mask_trace_data(metadata or {})
        propagation = (
            self._propagate_attributes(
                user_id=subject_id,
                session_id=session_id,
                metadata=safe_metadata,
                version=self.settings.langfuse_release or None,
                tags=tags or [],
                trace_name=name,
            )
            if self._propagate_attributes
            else nullcontext()
        )
        stack = ExitStack()
        try:
            stack.enter_context(propagation)
            observation_context = self.client.start_as_current_observation(
                as_type="span",
                name=name,
                input=mask_trace_data(input_data),
                metadata=safe_metadata,
                version=self.settings.langfuse_release or None,
            )
            observation = stack.enter_context(observation_context)
        except Exception:  # pragma: no cover - SDK initialization failure
            stack.close()
            logger.debug("Langfuse trace could not be started.", exc_info=True)
            yield _NoopObservation()
            return
        with stack:
            yield _SafeObservation(observation)

    @contextmanager
    def observation(
        self,
        *,
        name: str,
        observation_type: ObservationType,
        input_data: Any = None,
        metadata: dict[str, Any] | None = None,
        version: str | None = None,
        model: str | None = None,
        model_parameters: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        propagate: bool = False,
    ) -> Iterator[_SafeObservation | _NoopObservation]:
        if self.client is None:
            yield _NoopObservation()
            return

        safe_metadata = mask_trace_data(metadata or {})
        try:
            observation_context = self.client.start_as_current_observation(
                as_type=observation_type,
                name=name,
                input=mask_trace_data(input_data),
                metadata=safe_metadata,
                version=version,
                model=model,
                model_parameters=model_parameters,
            )
        except Exception:  # pragma: no cover - SDK initialization failure
            logger.debug("Langfuse observation could not be started.", exc_info=True)
            yield _NoopObservation()
            return

        with observation_context as observation:
            safe_observation = _SafeObservation(observation)
            if not propagate or self._propagate_attributes is None:
                yield safe_observation
                return
            with self._propagate_attributes(
                metadata=safe_metadata,
                version=version,
                tags=tags,
                trace_name=name,
            ):
                yield safe_observation

    def generation(
        self,
        *,
        name: str,
        model: str,
        input_data: Any,
        observation_type: Literal["generation", "embedding"] = "generation",
        metadata: dict[str, Any] | None = None,
        version: str | None = None,
        model_parameters: dict[str, Any] | None = None,
    ):
        return self.observation(
            name=name,
            observation_type=observation_type,
            input_data=input_data,
            metadata={
                "provider": self.settings.ai_provider,
                "provider_model": model,
                **(metadata or {}),
            },
            version=version or self.settings.langfuse_release or None,
            model=self.model_name(model),
            model_parameters=model_parameters,
        )

    def workflow(
        self,
        *,
        name: str,
        input_data: Any,
        metadata: dict[str, Any],
        version: str | None = None,
        tags: list[str] | None = None,
    ):
        return self.observation(
            name=name,
            observation_type="span",
            input_data=input_data,
            metadata=metadata,
            version=version,
            tags=tags,
            propagate=True,
        )

    def flush(self) -> None:
        if self.client is None:
            return
        try:
            self.client.flush()
        except Exception:  # pragma: no cover - SDK/network-specific failure
            logger.debug("Langfuse flush failed.", exc_info=True)


@lru_cache
def get_langfuse_tracer() -> LangfuseTracer:
    return LangfuseTracer(get_settings())
