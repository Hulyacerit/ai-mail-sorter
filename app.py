from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google.api_core import exceptions as google_api_exceptions

from core.agent import MailAgent


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            .hero-title {
                font-size: clamp(1.75rem, 4vw, 2.35rem);
                font-weight: 700;
                letter-spacing: -0.02em;
                margin: 0 0 0.35rem 0;
                line-height: 1.2;
            }
            .hero-sub {
                color: rgba(49, 51, 63, 0.75);
                font-size: 1rem;
                margin: 0 0 1.25rem 0;
            }
            @media (prefers-color-scheme: dark) {
                .hero-sub { color: rgba(250, 250, 250, 0.72); }
            }
            div[data-testid="stMetric"] {
                background: rgba(99, 102, 241, 0.08);
                padding: 1rem 1.1rem;
                border-radius: 0.75rem;
                border: 1px solid rgba(99, 102, 241, 0.22);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_mail_agent() -> MailAgent:
    if "mail_agent" not in st.session_state:
        st.session_state.mail_agent = MailAgent()
    return st.session_state.mail_agent


def main() -> None:
    app_root = Path(__file__).resolve().parent
    load_dotenv(app_root / ".env")
    load_dotenv()

    st.set_page_config(
        page_title="🤖 Kurumsal AI Mail Asistanı",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_styles()

    st.markdown(
        '<p class="hero-title">🤖 Kurumsal AI Mail Asistanı</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="hero-sub">E-postanızı yapıştırın; kategori, aciliyet ve '
        "profesyonel bir yanıt taslağı üretelim.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    mail_text = st.text_area(
        "E-posta metni",
        height=280,
        placeholder=(
            "Örn: Konu ve gövdeyi buraya yapıştırın…\n\n"
            "Merhaba,\nÜrün teslimatım gecikti, durumu öğrenebilir miyim?\n\nTeşekkürler."
        ),
        label_visibility="collapsed",
        key="mail_input",
    )

    analyze = st.button("Analiz Et", type="primary", use_container_width=False)

    if analyze:
        if not mail_text.strip():
            st.warning("Lütfen analiz edilecek e-posta metnini girin.")
            return

        try:
            with st.spinner("Yapay zeka maili okuyor..."):
                agent = _get_mail_agent()
                result = agent.analyze_mail(mail_text)
        except ValueError as exc:
            st.session_state.pop("mail_agent", None)
            st.error(str(exc))
            return
        except (
            google_api_exceptions.GoogleAPIError,
            ConnectionError,
            TimeoutError,
            OSError,
        ) as exc:
            st.error(f"Bağlantı veya API hatası: {exc}")
            return
        except Exception as exc:
            st.error(f"Beklenmeyen bir hata oluştu: {exc}")
            return

        is_system_error = result.get("kategori") == "Sistem"
        if is_system_error:
            st.error(result.get("taslak_cevap", "Analiz tamamlanamadı."))
            st.caption(
                "Bu durumda kategori ve aciliyet metrikleri analiz sonucu değildir; "
                "yalnızca hata bilgisidir."
            )

        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.metric(label="Kategori", value=result.get("kategori", "—"))
        with c2:
            st.metric(label="Aciliyet", value=result.get("aciliyet", "—"))

        st.subheader("Taslak yanıt" if not is_system_error else "Ayrıntı / kopyalanabilir metin")
        draft = result.get("taslak_cevap", "")
        if not is_system_error:
            st.success(
                "Aşağıdaki metni seçip kopyalayabilir veya sağ üstteki kopya ile alabilirsiniz."
            )
        st.code(draft, language=None)


if __name__ == "__main__":
    main()
