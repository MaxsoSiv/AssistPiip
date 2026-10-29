import json
import logging
import random
import re
import time

import requests

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 90


class LLMError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code

    @property
    def user_message(self) -> str:
        return {
            "auth": "Провайдер отклонил API-ключ. Проверьте ключ и доступ к модели.",
            "not_found": "Модель или адрес сервера не найдены. Проверьте имя модели и Base URL.",
            "rate_limit": "Провайдер ограничил частоту запросов. Попробуйте позже.",
            "quota": "Закончился лимит или баланс у провайдера.",
            "cancelled": "Запрос прерван.",
            "network": "Не удалось соединиться с провайдером. Проверьте интернет и адрес.",
            "server": "Провайдер временно недоступен.",
            "bad_response": "Провайдер вернул неожиданный ответ.",
        }.get(self.code, self.args[0] if self.args else "Неизвестная ошибка LLM")


def _backoff_delay(attempt: int, retry_after: float | None) -> float:
    if retry_after:
        return min(max(retry_after, 0.5), 30.0)
    return min(1.0 * (2 ** attempt) + random.uniform(0, 0.5), 15.0)


def _friendly_status(status: int) -> LLMError:
    if status in (401, 403):
        return LLMError("auth", f"HTTP {status}")
    if status == 402:
        return LLMError("quota", "HTTP 402")
    if status == 404:
        return LLMError("not_found", f"HTTP {status}")
    if status == 429:
        return LLMError("rate_limit", "HTTP 429")
    if status >= 500:
        return LLMError("server", f"HTTP {status}")
    return LLMError("bad_response", f"HTTP {status}")


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str,
                 temperature: float = 0.7, max_tokens: int = 1024):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, messages: list[dict], on_delta=None, cancel=None) -> dict:
        if not self.base_url or not self.model:
            raise LLMError("config", "AI-ассистент настроен не полностью")
        if not self.api_key:
            raise LLMError("config", "Не задан API-ключ")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": on_delta is not None,
        }
        url = self.base_url + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        last_error = None
        for attempt in range(MAX_ATTEMPTS):
            if cancel is not None and cancel.is_set():
                raise LLMError("cancelled", "cancelled")
            try:
                return self._request(url, headers, payload, on_delta, cancel)
            except LLMError as e:
                if e.code in ("cancelled", "auth", "not_found", "quota", "config", "bad_response"):
                    raise
                last_error = e
            except requests.RequestException as e:
                last_error = LLMError("network", str(e))

            if attempt < MAX_ATTEMPTS - 1:
                delay = _backoff_delay(attempt, getattr(last_error, "retry_after", None))
                if cancel is not None:
                    if cancel.wait(delay):
                        raise LLMError("cancelled", "cancelled")
                else:
                    time.sleep(delay)

        raise last_error or LLMError("network", "unknown")

    def _request(self, url, headers, payload, on_delta, cancel) -> dict:
        stream = on_delta is not None
        resp = requests.post(
            url, json=payload, headers=headers, stream=stream,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
        if resp.status_code != 200:
            retry_after = None
            if resp.status_code == 429:
                retry_after = _parse_retry_after(resp.headers.get("Retry-After"))
            err = _friendly_status(resp.status_code)
            err.retry_after = retry_after
            logging.warning(f"LLM HTTP {resp.status_code}: {resp.text[:200]}")
            raise err

        if not stream:
            data = resp.json()
            try:
                content = data["choices"][0]["message"]["content"] or ""
            except (KeyError, IndexError, TypeError) as e:
                raise LLMError("bad_response", str(e)) from e
            return {"content": content, "usage": data.get("usage")}

        content_parts = []
        usage = None
        try:
            for raw in resp.iter_lines():
                if cancel is not None and cancel.is_set():
                    raise LLMError("cancelled", "cancelled")
                line = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else (raw or "")
                if not line or not line.startswith("data:"):
                    continue
                body = line[5:].strip()
                if body == "[DONE]":
                    break
                try:
                    chunk = json.loads(body)
                except json.JSONDecodeError:
                    continue
                usage = chunk.get("usage") or usage
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = (choices[0].get("delta") or {}).get("content")
                if delta:
                    content_parts.append(delta)
                    on_delta(delta)
        except LLMError:
            raise
        except (requests.RequestException, json.JSONDecodeError) as e:
            if content_parts:
                return {"content": "".join(content_parts), "usage": usage}
            raise LLMError("bad_response", str(e)) from e

        if not content_parts:
            raise LLMError("bad_response", "empty stream")
        return {"content": "".join(content_parts), "usage": usage}


def _parse_retry_after(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()
