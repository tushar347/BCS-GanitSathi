from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Optional, TypeVar
from urllib import error as urllib_error
from urllib import request as urllib_request

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelGateway:
    def __init__(
        self,
        model_path: Optional[str] = None,
        callable_backend: Optional[Callable[[str, str], Any]] = None,
        provider: Optional[str] = None,
        ollama_model: Optional[str] = None,
        ollama_url: Optional[str] = None,
        max_new_tokens: int = 256,
        device: Optional[str] = None,
    ):
        self.provider = self._normalize_provider(provider or os.getenv("GONITSATHI_MODEL_PROVIDER") or "fallback")
        self.model_path = model_path or os.getenv("GONITSATHI_MODEL_PATH")
        self.ollama_model = (ollama_model or os.getenv("GONITSATHI_OLLAMA_MODEL") or "qwen3:latest").strip()
        self.ollama_url = (ollama_url or os.getenv("GONITSATHI_OLLAMA_URL") or "http://localhost:11434").rstrip("/")
        self.callable_backend = callable_backend
        self.max_new_tokens = max_new_tokens
        self.device = device
        self._tokenizer = None
        self._model = None
        self.call_count = 0
        self.failed_call_count = 0
        self.last_call_metadata: dict[str, Any] = {}
        self.last_error: Optional[str] = None

    @property
    def available(self) -> bool:
        if self.callable_backend is not None:
            return True
        if self.provider == "transformers":
            return bool(self.model_path)
        if self.provider == "ollama":
            return bool(self.ollama_model)
        return False

    @property
    def neural_call_count(self) -> int:
        return self.call_count

    def _normalize_provider(self, provider: str) -> str:
        value = (provider or "fallback").strip().lower()
        if value not in {"fallback", "transformers", "ollama"}:
            return "fallback"
        return value

    def _record_success(self, *, provider: str, model: str, latency_ms: float, prompt_tokens: Optional[int], generated_tokens: Optional[int]) -> None:
        self.call_count += 1
        self.last_call_metadata = {
            "provider": provider,
            "model": model,
            "neural_call_count": self.call_count,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "generated_tokens": generated_tokens,
            "status": "success",
            "fallback_status": "not_used",
            "failure_reason": None,
        }
        self.last_error = None

    def _record_failure(self, *, provider: str, model: str, error: str) -> None:
        self.failed_call_count += 1
        self.last_call_metadata = {
            "provider": provider,
            "model": model,
            "neural_call_count": self.call_count,
            "latency_ms": None,
            "prompt_tokens": None,
            "generated_tokens": None,
            "status": "failure",
            "fallback_status": "not_used",
            "failure_reason": error,
        }
        self.last_error = error

    def _load_huggingface(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        if not self.model_path:
            raise RuntimeError("No local model path configured")
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            local_files_only=True,
            trust_remote_code=True,
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            local_files_only=True,
            trust_remote_code=True,
            torch_dtype="auto",
        )
        target_device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(target_device)
        self._model.eval()
        self.device = target_device

    def _generate_ollama(self, system_prompt: str, user_prompt: str) -> str:
        if not self.ollama_model:
            raise RuntimeError("Ollama model is not configured")
        base_url = self.ollama_url.rstrip("/")
        endpoint = f"{base_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0,
                "num_predict": max(32, min(int(self.max_new_tokens), 2048)),
            },
        }
        start_time = time.perf_counter()
        try:
            request = urllib_request.Request(
                endpoint,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib_request.urlopen(request, timeout=30) as response:
                    content = response.read()
            except TypeError:
                with urllib_request.urlopen(request) as response:
                    content = response.read()
            data = json.loads(content.decode("utf-8"))
            result = data.get("response", "")
            if not isinstance(result, str):
                raise RuntimeError("Malformed Ollama response")
            if not result.strip():
                raise RuntimeError("Ollama returned empty response")
            latency_ms = round((time.perf_counter() - start_time) * 1000, 3)
            prompt_tokens = data.get("prompt_eval_count")
            generated_tokens = data.get("eval_count")
            self._record_success(
                provider="ollama",
                model=self.ollama_model,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                generated_tokens=generated_tokens,
            )
            self.last_call_metadata["latency"] = latency_ms
            self.last_call_metadata["total_duration"] = data.get("total_duration")
            self.last_call_metadata["load_duration"] = data.get("load_duration")
            return result.strip()
        except (urllib_error.URLError, urllib_error.HTTPError, TimeoutError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 3)
            message = str(exc)
            if isinstance(exc, urllib_error.URLError):
                message = "Ollama provider selected but local Ollama service is unavailable."
            self._record_failure(provider="ollama", model=self.ollama_model, error=message)
            self.last_call_metadata["latency"] = latency_ms
            raise RuntimeError(message) from exc

    def _generate_transformers(self, system_prompt: str, user_prompt: str) -> str:
        self._load_huggingface()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            text = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            text = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        encoded = self._tokenizer(text, return_tensors="pt")
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        generated = self._model.generate(
            **encoded,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            pad_token_id=self._tokenizer.eos_token_id,
        )
        input_len = encoded["input_ids"].shape[1]
        completion = generated[0][input_len:]
        result = self._tokenizer.decode(completion, skip_special_tokens=True).strip()
        self._record_success(
            provider="transformers",
            model=self.model_path or "transformers",
            latency_ms=0.0,
            prompt_tokens=None,
            generated_tokens=None,
        )
        return result

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        if self.callable_backend is not None:
            result = self.callable_backend(system_prompt, user_prompt)
            if isinstance(result, str):
                self._record_success(provider="callable", model="callable_backend", latency_ms=0.0, prompt_tokens=None, generated_tokens=None)
                return result
            serialized = json.dumps(result, ensure_ascii=False)
            self._record_success(provider="callable", model="callable_backend", latency_ms=0.0, prompt_tokens=None, generated_tokens=None)
            return serialized
        provider = self._normalize_provider(self.provider)
        if provider == "ollama":
            return self._generate_ollama(system_prompt, user_prompt)
        if provider == "transformers":
            if not self.model_path:
                raise RuntimeError("Transformers provider selected but no model path is configured")
            return self._generate_transformers(system_prompt, user_prompt)
        if self.model_path:
            return self._generate_transformers(system_prompt, user_prompt)
        raise RuntimeError("No neural model provider configured; using deterministic fallback instead.")

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
    ) -> Optional[T]:
        if not self.available:
            return None
        try:
            raw = self.generate_text(system_prompt, user_prompt)
        except Exception as exc:
            self.last_error = str(exc)
            self._record_failure(provider=self.provider, model=self.ollama_model if self.provider == "ollama" else (self.model_path or self.provider), error=str(exc))
            return None
        payload = self._extract_json(raw)
        if payload is None:
            self._record_failure(provider=self.provider, model=self.ollama_model if self.provider == "ollama" else (self.model_path or self.provider), error="Malformed structured response")
            return None
        try:
            return schema.model_validate(payload)
        except Exception:
            self._record_failure(provider=self.provider, model=self.ollama_model if self.provider == "ollama" else (self.model_path or self.provider), error="Pydantic validation failed")
            return None

    def reset_counters(self) -> None:
        self.call_count = 0
        self.failed_call_count = 0
        self.last_call_metadata = {}
        self.last_error = None

    def check_ollama_ready(self) -> tuple[bool, str]:
        if self.provider != "ollama":
            return True, "provider_not_selected"
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": "Reply with JSON and no extra text: {\"status\":\"ok\"}",
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "num_predict": 32},
            }
            request = urllib_request.Request(
                f"{self.ollama_url.rstrip('/')}/api/generate",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib_request.urlopen(request, timeout=30) as response:
                    data = json.loads(response.read().decode("utf-8"))
            except TypeError:
                with urllib_request.urlopen(request) as response:
                    data = json.loads(response.read().decode("utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("response"), str) or not data["response"].strip():
                return False, f"Model {self.ollama_model} could not generate a response from Ollama."
            return True, "ok"
        except Exception:
            return False, "Ollama provider selected but local Ollama service is unavailable."

    def _extract_json(self, raw: str) -> Optional[dict[str, Any]]:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            value = json.loads(text)
            return value if isinstance(value, dict) else None
        except Exception:
            pass
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                value, _ = decoder.raw_decode(text[index:])
                if isinstance(value, dict):
                    return value
            except Exception:
                continue
        return None
