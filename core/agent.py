from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TypedDict

import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core import exceptions as google_api_exceptions

logger = logging.getLogger(__name__)


class MailAnalysis(TypedDict):
    """Gemini çıktısının şeması (API zorunlu alanları)."""

    kategori: str
    aciliyet: str
    taslak_cevap: str


_REQUIRED_KEYS = frozenset(MailAnalysis.__annotations__.keys())

_SYSTEM_INSTRUCTION = """\
Sen bir iş e-postası analisti ve müşteri iletişim uzmanısın.
Verilen e-postayı analiz et ve çıktıyı yalnızca Türkçe üret.

Kurallar:
- "kategori": E-postanın ana amacına uygun tek bir iş kategorisi (örnekler: Destek, Satış, İK, Teknik, Faturalama, Genel, Şikayet, Bilgi Talebi). Uygunsa başka kısa bir etiket de kullanabilirsin.
- "aciliyet": Yalnızca şu üç değerden biri olmalı: Düşük, Orta, Yüksek.
- "taslak_cevap": Göndericiye gönderilebilecek, kısa, net ve profesyonel bir Türkçe yanıt taslağı; nazik ve çözüm odaklı olsun.
"""


# Google bu anahtar/v1beta kombinasyonunda 1.5 sürümlü adları kaldırmış olabiliyor; API’de
# “Flash” için güncel takma ad ve hızlı yedekler (list_models ile doğrulanabilir).
_DEFAULT_MODEL_CHAIN: tuple[str, ...] = (
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
)


def _model_chain_from_env() -> tuple[str, ...]:
    """GEMINI_MODEL: tek model veya virgülle ayrılmış öncelik (ör. gemini-flash-latest,gemini-2.5-flash)."""
    raw = os.getenv("GEMINI_MODEL", "").strip()
    if not raw:
        return _DEFAULT_MODEL_CHAIN
    parts = tuple(p.strip() for p in raw.split(",") if p.strip())
    return parts if parts else _DEFAULT_MODEL_CHAIN


def _format_api_error(exc: google_api_exceptions.GoogleAPIError) -> str:
    text = str(exc)
    if isinstance(exc, google_api_exceptions.ResourceExhausted) or "429" in text:
        return (
            "Gemini API kotası doldu veya bu model için ücretsiz planda istek kapalı görünüyor. "
            "Bir süre bekleyip tekrar deneyin; Google AI Studio üzerinden kota veya faturalandırmayı kontrol edin. "
            "İsterseniz .env içinde GEMINI_MODEL ile başka bir model sırası tanımlayabilirsiniz.\n\n"
            f"Teknik özet: {text[:900]}"
        )
    if isinstance(exc, google_api_exceptions.NotFound):
        return (
            "Bu model adı bu API sürümü veya anahtarınız için yok. Eski adlar (ör. gemini-1.5-flash-002) "
            "kaldırılmış olabilir. .env içinde GEMINI_MODEL ile deneyin: gemini-flash-latest veya gemini-2.5-flash. "
            "Tam listeyi görmek için Python’da genai.list_models() kullanın.\n\n"
            f"Teknik özet: {text[:900]}"
        )
    return f"Servis hatası: {text[:900]}"


class MailAgent:
    """Gemini kullanarak e-posta içeriği analizi."""

    DEFAULT_MODEL_CHAIN: tuple[str, ...] = _DEFAULT_MODEL_CHAIN

    def __init__(self, model_name: str | None = None) -> None:
        project_root = Path(__file__).resolve().parent.parent
        load_dotenv(project_root / ".env")
        load_dotenv()

        api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY bulunamadı. Proje kökündeki .env dosyasına şunu ekleyin: "
                "GEMINI_API_KEY=your_key (Google örneklerinde bazen GOOGLE_API_KEY kullanılır; "
                "ikisi de desteklenir). Yanlış isim (ör. GEOPY_API_KEY) çalışmaz."
            )

        genai.configure(api_key=str(api_key).strip())

        self._model_chain: tuple[str, ...] = (
            (model_name.strip(),) if model_name and model_name.strip() else _model_chain_from_env()
        )
        self._locked_model: str | None = None
        self._generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=MailAnalysis,
            temperature=0.2,
        )

    @property
    def model_name(self) -> str:
        """Şu an tercih edilen veya son başarılı model."""
        if self._locked_model:
            return self._locked_model
        return self._model_chain[0] if self._model_chain else ""

    def _build_model(self, model_id: str) -> genai.GenerativeModel:
        return genai.GenerativeModel(
            model_name=model_id,
            generation_config=self._generation_config,
            system_instruction=_SYSTEM_INSTRUCTION,
        )

    def _model_try_order(self) -> list[str]:
        chain = list(self._model_chain)
        if self._locked_model and self._locked_model in chain:
            return [self._locked_model] + [m for m in chain if m != self._locked_model]
        return chain

    def analyze_mail(self, mail_text: str) -> dict[str, str]:
        stripped = mail_text.strip() if isinstance(mail_text, str) else ""
        if not stripped:
            return {
                "kategori": "Genel",
                "aciliyet": "Düşük",
                "taslak_cevap": (
                    "Analiz için e-posta metni gerekli. Lütfen içeriği paylaşıp tekrar deneyin."
                ),
            }

        user_prompt = (
            "Aşağıdaki e-postayı JSON şemasına uygun olarak analiz et.\n\n"
            "--- E-POSTA ---\n"
            f"{stripped}\n"
            "--- SON ---"
        )

        last_api_error: google_api_exceptions.GoogleAPIError | None = None

        for model_id in self._model_try_order():
            try:
                model = self._build_model(model_id)
                response = model.generate_content(user_prompt)
            except (ConnectionError, TimeoutError, OSError) as exc:
                logger.exception("Ağ bağlantı hatası: %s", exc)
                return self._fallback_error_response(
                    "Bağlantı sorunu oluştu. İnternetinizi kontrol edip yeniden deneyin."
                )
            except google_api_exceptions.NotFound as exc:
                last_api_error = exc
                logger.warning("Model kullanılamıyor, sıradaki denenecek: %s — %s", model_id, exc)
                continue
            except google_api_exceptions.ResourceExhausted as exc:
                last_api_error = exc
                logger.warning("Kota/limit: %s — sıradaki model denenecek: %s", model_id, exc)
                continue
            except google_api_exceptions.GoogleAPIError as exc:
                logger.exception("Google API hatası: %s", exc)
                return self._fallback_error_response(_format_api_error(exc))

            try:
                candidate = getattr(response, "text", None)
                if candidate is None or not str(candidate).strip():
                    block_reason = getattr(
                        getattr(response, "prompt_feedback", None), "block_reason", None
                    )
                    logger.warning("Gemini boş veya bloklu yanıt: block_reason=%s", block_reason)
                    raise ValueError("Model boş veya bloklu yanıt döndü.")

                parsed = json.loads(response.text)

            except json.JSONDecodeError as exc:
                logger.exception("JSON ayrıştırma hatası: %s", exc)
                return self._fallback_error_response(
                    "Model yanıtı beklenen formatta değil. Lütfen tekrar deneyin."
                )
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                logger.exception("Yanıt işleme hatası: %s", exc)
                return self._fallback_error_response(
                    "Yanıt işlenemedi. Lütfen tekrar deneyin."
                )
            except Exception as exc:
                logger.exception("Beklenmeyen hata: %s", exc)
                return self._fallback_error_response(
                    "Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin."
                )

            validated = self._coerce_analysis_dict(parsed)
            if validated is None:
                return self._fallback_error_response(
                    "Model çıktısı gerekli alanları içermiyor. Lütfen tekrar deneyin."
                )
            self._locked_model = model_id
            return validated

        if last_api_error is not None:
            return self._fallback_error_response(_format_api_error(last_api_error))
        return self._fallback_error_response(
            "Yapılandırılmış model listesi boş. GEMINI_MODEL veya MailAgent(model_name=...) kontrol edin."
        )

    def classify(self, subject: str, body: str) -> dict[str, str]:
        return self.analyze_mail(f"Konu: {subject}\n\n{body}")

    @staticmethod
    def _coerce_analysis_dict(raw: object) -> dict[str, str] | None:
        if not isinstance(raw, dict):
            return None
        out: dict[str, str] = {}
        for key in _REQUIRED_KEYS:
            val = raw.get(key)
            if val is None or not isinstance(val, str) or not val.strip():
                return None
            out[key] = val.strip()
        return out

    @staticmethod
    def _fallback_error_response(message: str) -> dict[str, str]:
        return {
            "kategori": "Sistem",
            "aciliyet": "Düşük",
            "taslak_cevap": message,
        }
