import os
import tempfile

import streamlit as st

from app import transcribe_audio, format_with_gemini, ALLOWED_AUDIO_EXTENSIONS, ALLOWED_TEXT_EXTENSIONS


def main():
    st.set_page_config(
        page_title="AI Scribe",
        layout="wide",
        page_icon="🩺",
    )

    st.markdown(
        """
        <style>
        /* Overall page background */
        html, body, [data-testid="stAppViewContainer"], .main, .block-container {
            background:
                radial-gradient(circle at top left, rgba(56,189,248,0.18), transparent 55%),
                radial-gradient(circle at bottom right, rgba(129,140,248,0.22), transparent 55%),
                #020617 !important;
            color: #e5e7eb;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
        }
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        .block-container {
            padding-top: 1.6rem;
        }
        .ai-scribe-header {
            padding: 1.25rem 1.5rem;
            border-radius: 0.9rem;
            background: radial-gradient(circle at top left, rgba(59,130,246,0.42), rgba(56,189,248,0.12));
            border: 1px solid rgba(148,163,184,0.45);
            box-shadow: 0 22px 55px rgba(15,23,42,0.85);
            backdrop-filter: blur(14px);
        }
        .metric-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.15rem 0.75rem;
            border-radius: 999px;
            background: radial-gradient(circle at top left, rgba(15,23,42,0.85), rgba(15,23,42,0.4));
            border: 1px solid rgba(148,163,184,0.55);
            font-size: 0.78rem;
            color: #e5e7eb;
        }
        .section-card {
            padding: 1.25rem 1.25rem 1.1rem 1.25rem;
            border-radius: 0.9rem;
            background: linear-gradient(145deg, rgba(15,23,42,0.96), rgba(15,23,42,0.82));
            border: 1px solid rgba(31,41,55,0.98);
            box-shadow: 0 18px 45px rgba(15,23,42,0.9);
            backdrop-filter: blur(18px);
            transition: transform 0.18s ease-out, box-shadow 0.18s ease-out, border-color 0.18s ease-out;
        }
        .section-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 24px 65px rgba(15,23,42,0.95);
            border-color: rgba(59,130,246,0.6);
        }
        .section-card h3 {
            font-size: 0.95rem;
            color: #e5e7eb;
            margin-bottom: 0.6rem;
        }
        .small-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #9ca3af;
        }
        /* Sidebar */
        [data-testid="stSidebar"] > div {
            background: radial-gradient(circle at top left, rgba(15,23,42,0.96), rgba(15,23,42,0.96));
            border-right: 1px solid rgba(31,41,55,0.9);
        }
        .sidebar-card {
            padding: 1.1rem 1rem;
            border-radius: 0.9rem;
            background: radial-gradient(circle at top left, rgba(15,23,42,0.98), rgba(15,23,42,0.9));
            border: 1px solid rgba(31,41,55,0.95);
            box-shadow: 0 18px 40px rgba(15,23,42,0.9);
        }
        .sidebar-card h3 {
            margin-top: 0;
            margin-bottom: 0.4rem;
            font-size: 1rem;
        }
        .sidebar-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.1rem 0.6rem;
            border-radius: 999px;
            background: rgba(15,23,42,0.9);
            border: 1px solid rgba(55,65,81,0.9);
            font-size: 0.72rem;
            color: #9ca3af;
        }
        .sidebar-step {
            font-size: 0.85rem;
            color: #9ca3af;
            margin-bottom: 0.25rem;
        }
        .sidebar-step span {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.05rem;
            height: 1.05rem;
            border-radius: 999px;
            background: rgba(31,41,55,0.95);
            color: #e5e7eb;
            font-size: 0.72rem;
            margin-right: 0.35rem;
        }
        /* Buttons */
        .stButton>button {
            border-radius: 999px;
            border: 1px solid rgba(59,130,246,0.75);
            background: linear-gradient(135deg, #2563eb, #22c55e);
            color: #f9fafb;
            font-weight: 500;
            font-size: 0.9rem;
            padding: 0.45rem 1rem;
            box-shadow: 0 12px 35px rgba(37,99,235,0.55);
            transition: transform 0.12s ease-out, box-shadow 0.12s ease-out, filter 0.12s ease-out;
        }
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 45px rgba(37,99,235,0.75);
            filter: brightness(1.05);
        }
        .stButton>button:active {
            transform: translateY(0px) scale(0.99);
            box-shadow: 0 8px 24px rgba(15,23,42,0.9);
        }
        .footer-note {
            font-size: 0.78rem;
            color: #6b7280;
            text-align: center;
            padding-top: 0.8rem;
        }
        /* Text areas inside cards */
        textarea {
            background-color: #020617 !important;
            color: #e5e7eb !important;
            border-radius: 0.6rem !important;
            border: 1px solid rgba(55,65,81,0.9) !important;
        }
        textarea:focus {
            border-color: rgba(59,130,246,0.85) !important;
            box-shadow: 0 0 0 1px rgba(59,130,246,0.85) !important;
        }
        /* File uploader */
        [data-testid="stFileUploader"] > div {
            background-color: rgba(15,23,42,0.85);
            border-radius: 0.75rem;
            border: 1px dashed rgba(75,85,99,0.85);
        }
        [data-testid="stFileUploader"] section {
            color: #9ca3af;
        }
        /* Tabs */
        [data-baseweb="tab-list"] {
            border-radius: 999px;
            padding: 0.25rem;
            background: radial-gradient(circle at top left, rgba(15,23,42,0.98), rgba(17,24,39,0.98));
            border: 1px solid rgba(31,41,55,0.95);
        }
        [data-baseweb="tab"] {
            border-radius: 999px !important;
            padding: 0.35rem 0.9rem !important;
            color: #9ca3af !important;
            font-size: 0.86rem !important;
        }
        [aria-selected="true"][data-baseweb="tab"] {
            background: linear-gradient(135deg, rgba(59,130,246,0.9), rgba(56,189,248,0.9)) !important;
            color: #f9fafb !important;
            box-shadow: 0 12px 30px rgba(37,99,235,0.6);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-card">
                <div class="sidebar-pill">AI-powered clinical documentation</div>
                <h3>AI Scribe</h3>
                <p style="font-size: 0.86rem; color: #9ca3af; margin-bottom: 0.75rem;">
                    Turn raw consultation audio or free text into clear, structured clinical notes ready for your EHR.
                </p>
                <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.12em; color: #6b7280; margin-bottom: 0.35rem;">Workflow</div>
                <div class="sidebar-step"><span>1</span>Choose template type</div>
                <div class="sidebar-step"><span>2</span>Upload audio or paste text</div>
                <div class="sidebar-step"><span>3</span>Generate & refine the note</div>
                <div class="sidebar-step"><span>4</span>Download or paste into your system</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    header_col, template_col = st.columns([3, 2])

    with header_col:
        st.markdown(
            """
            <div class="ai-scribe-header">
                <div class="metric-pill">Clinical note assistant · Powered by Gemini</div>
                <h1 style="margin-top: 0.7rem; margin-bottom: 0.25rem; color: #e5e7eb;">AI Scribe</h1>
                <p style="margin: 0; color: #cbd5f5; font-size: 0.93rem;">
                    Upload a consultation recording or paste free text and convert it into a clean, structured clinical note.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with template_col:
        st.markdown("<span class='small-label'>Template</span>", unsafe_allow_html=True)
        template_type = st.selectbox(
            "Template type",
            ["SOAP Note", "H&P Note"],
            index=0,
            label_visibility="collapsed",
        )

    st.markdown("")
    tab_audio, tab_text = st.tabs(["🎙️ Audio to Note", "📝 Text to Note"])

    with tab_audio:
        left_col, right_col = st.columns([1, 1])

        with left_col:
            with st.container():
                st.markdown("<div class='section-card'>", unsafe_allow_html=True)
                st.markdown("<h3>Audio upload</h3>", unsafe_allow_html=True)
                audio_file = st.file_uploader(
                    "Upload audio file",
                    type=list(ALLOWED_AUDIO_EXTENSIONS),
                    key="audio_uploader",
                )
                generate_audio = st.button("Generate note from audio", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with right_col:
            with st.container():
                st.markdown("<div class='section-card'>", unsafe_allow_html=True)
                st.markdown("<h3>Output preview</h3>", unsafe_allow_html=True)
                transcript_placeholder = st.empty()
                note_placeholder = st.empty()
                download_placeholder = st.empty()
                st.markdown("</div>", unsafe_allow_html=True)

        if generate_audio:
            if not audio_file:
                st.error("No audio file provided")
            else:
                suffix = os.path.splitext(audio_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(audio_file.read())
                    tmp_path = tmp.name

                try:
                    with st.spinner("Transcribing audio with AssemblyAI..."):
                        transcript_text = transcribe_audio(tmp_path)

                    with st.spinner("Formatting with Gemini..."):
                        formatted_output = format_with_gemini(transcript_text, template_type)

                    st.success("Clinical note generated")
                    with transcript_placeholder.container():
                        with st.expander("Original transcript", expanded=False):
                            st.text_area(
                                "Transcript",
                                transcript_text,
                                height=220,
                                label_visibility="collapsed",
                            )

                    with note_placeholder.container():
                        st.subheader("Structured note")
                        st.text_area(
                            "Note",
                            formatted_output,
                            height=400,
                            label_visibility="collapsed",
                        )

                    with download_placeholder:
                        st.download_button(
                            label="Download note",
                            data=formatted_output,
                            file_name="note.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(str(e))
                finally:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

    with tab_text:
        input_col, output_col = st.columns([1, 1])

        with input_col:
            with st.container():
                st.markdown("<div class='section-card'>", unsafe_allow_html=True)
                st.markdown("<h3>Text input</h3>", unsafe_allow_html=True)
                text_input = st.text_area("Paste text here", height=200)
                generate_text = st.button("Generate note from text", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with output_col:
            with st.container():
                st.markdown("<div class='section-card'>", unsafe_allow_html=True)
                st.markdown("<h3>Output preview</h3>", unsafe_allow_html=True)
                text_input_placeholder = st.empty()
                text_note_placeholder = st.empty()
                text_download_placeholder = st.empty()
                st.markdown("</div>", unsafe_allow_html=True)

        if generate_text:
            content = text_input or ""

            if not content.strip():
                st.error("No text provided")
            else:
                try:
                    with st.spinner("Formatting with Gemini..."):
                        formatted_output = format_with_gemini(content, template_type)

                    st.success("Clinical note generated")
                    with text_input_placeholder.container():
                        with st.expander("Original text", expanded=False):
                            st.text_area(
                                "Input",
                                content,
                                height=220,
                                label_visibility="collapsed",
                            )

                    with text_note_placeholder.container():
                        st.subheader("Structured note")
                        st.text_area(
                            "Note",
                            formatted_output,
                            height=400,
                            label_visibility="collapsed",
                        )

                    with text_download_placeholder:
                        st.download_button(
                            label="Download note",
                            data=formatted_output,
                            file_name="note.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(str(e))


    st.markdown("<div class='footer-note'>AI Scribe is an assistive tool and does not replace clinical judgement. Please review all generated notes before use.</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
