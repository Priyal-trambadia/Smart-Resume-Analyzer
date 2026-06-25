import streamlit as st
import os
from dotenv import load_dotenv
from utils.pdf_parser import extract_text_from_pdf
from utils.ai_engine import (
    extract_skills_from_resume,
    extract_keywords_from_jd,
    get_skill_gap_analysis,
    improve_resume_bullets,
)
from utils.ats_scorer import compute_ats_score
from utils.report_generator import generate_pdf_report
import plotly.express as px
import plotly.graph_objects as go

# ── Config ──────────────────────────────────────────────────────────────
load_dotenv()
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 500;
    }
    .skill-chip {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        margin: 3px;
        font-size: 13px;
        font-weight: 500;
    }
    .chip-match   { background: #D1FAE5; color: #065F46; }
    .chip-missing { background: #FEE2E2; color: #991B1B; }
    .chip-neutral { background: #EDE9FE; color: #5B21B6; }
    .ats-score-box {
        text-align: center;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .score-high   { background: #D1FAE5; color: #065F46; }
    .score-medium { background: #FEF3C7; color: #92400E; }
    .score-low    { background: #FEE2E2; color: #991B1B; }
    .section-title {
        font-size: 16px;
        font-weight: 600;
        margin: 1rem 0 0.5rem;
        color: #1F2937;
    }
    .gap-card {
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        background: #FAFAFA;
    }
    .priority-high   { color: #DC2626; font-weight: 600; }
    .priority-medium { color: #D97706; font-weight: 600; }
    .priority-low    { color: #059669; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📄 Resume Analyzer")
    st.caption("Powered by Gemini AI")
    st.divider()

    st.markdown("**How to use:**")
    st.markdown("""
    1. Upload your resume (PDF)
    2. Paste a job description
    3. Click **Analyze**
    4. Review your ATS score & skill gaps
    5. Download your report
    """)

    st.divider()

    api_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Get your free key at aistudio.google.com",
    )

    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key

    st.divider()

    # Creator Card
   
    st.info("""
    👨‍💻 **Priyal Trambadia**

    AI/ML Engineer • Full Stack Developer

    Passionate about Machine Learning, Generative AI, and Building Intelligent Applications.
    """)

    st.divider()

    st.caption("Built with Streamlit + Gemini")


# ── Session State Init ───────────────────────────────────────────────────
for key in ["resume_text", "resume_skills", "jd_keywords", "ats_result",
            "gap_analysis", "improved_bullets", "analysis_done"]:
    if key not in st.session_state:
        st.session_state[key] = None
st.session_state.setdefault("analysis_done", False)


# ── Helper: check if a list contains API error strings ──────────────────
def has_api_error(data):
    """Returns True if any item in the list looks like an error string."""
    if not data:
        return False
    return any("Error" in str(item) or "error" in str(item).lower() for item in data)


# ── Main Tabs ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Upload & Input",
    "📊 ATS Score",
    "🔍 Skill Gap",
    "📥 Report",
])


# ════════════════════════════════════════════════════════════════════════
# TAB 1 — Upload & Input
# ════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Upload Your Resume")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("**Resume (PDF)**")
        uploaded_file = st.file_uploader(
            "Drop your resume here",
            type=["pdf"],
            label_visibility="collapsed",
        )
        if uploaded_file:
            with st.spinner("Extracting text from PDF..."):
                text = extract_text_from_pdf(uploaded_file)
                st.session_state.resume_text = text
            st.success(f"✅ Resume loaded — {len(text.split())} words extracted")
            with st.expander("Preview extracted text"):
                st.text(text[:2000] + ("..." if len(text) > 2000 else ""))

    with col2:
        st.markdown("**Job Description**")
        jd_text = st.text_area(
            "Paste the full job description here",
            height=280,
            placeholder="Paste the job description you want to match against...",
            label_visibility="collapsed",
        )

    st.divider()

    ready = (
        st.session_state.resume_text
        and jd_text.strip()
        and os.environ.get("GEMINI_API_KEY")
    )

    if not os.environ.get("GEMINI_API_KEY"):
        st.warning("⚠️ Add your Gemini API key in the sidebar to continue.")

    analyze_btn = st.button(
        "🚀 Analyze Resume",
        disabled=not ready,
        use_container_width=True,
        type="primary",
    )

    if analyze_btn:

        # ── STEP 1: Extract resume skills ────────────────────────────────
        with st.spinner("Extracting skills from resume..."):
            resume_skills = extract_skills_from_resume(st.session_state.resume_text)
            st.session_state.resume_skills = resume_skills

        # ── FIX: Guard against API error in resume skills ─────────────────
        if has_api_error(resume_skills):
            st.error(
                "❌ Failed to extract resume skills. "
                "Please check your Gemini API key and make sure it is valid. "
                "Also ensure you are using a supported model (gemini-2.0-flash)."
            )
            st.stop()

        # ── STEP 2: Extract JD keywords ──────────────────────────────────
        with st.spinner("Analyzing job description keywords..."):
            jd_keywords = extract_keywords_from_jd(jd_text)
            st.session_state.jd_keywords = jd_keywords

        # ── FIX: Guard against API error in JD keywords ───────────────────
        if has_api_error(jd_keywords):
            st.error(
                "❌ Failed to extract job description keywords. "
                "Please check your Gemini API key and make sure it is valid. "
                "Also ensure you are using a supported model (gemini-2.0-flash)."
            )
            st.stop()

        # ── STEP 3: Compute ATS score ────────────────────────────────────
        with st.spinner("Computing ATS score..."):
            ats_result = compute_ats_score(resume_skills, jd_keywords)
            st.session_state.ats_result = ats_result

        # ── STEP 4: Skill gap analysis ───────────────────────────────────
        with st.spinner("Running skill gap analysis with AI..."):
            st.session_state.gap_analysis = get_skill_gap_analysis(
                ats_result["missing"],
                jd_text[:500],
            )

        st.session_state.analysis_done = True
        st.success("✅ Analysis complete! Switch to the ATS Score tab.")
        st.balloons()


# ════════════════════════════════════════════════════════════════════════
# TAB 2 — ATS Score
# ════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.analysis_done:
        st.info("Upload your resume and paste a job description in Tab 1, then click Analyze.")
    else:
        result = st.session_state.ats_result
        score  = result["score"]

        # Score box
        if score >= 70:
            css_class, label = "score-high", "Strong Match 🟢"
        elif score >= 40:
            css_class, label = "score-medium", "Partial Match 🟡"
        else:
            css_class, label = "score-low", "Weak Match 🔴"

        st.markdown(f"""
        <div class="ats-score-box {css_class}">
            <div style="font-size:56px;font-weight:700;line-height:1">{score}%</div>
            <div style="font-size:18px;margin-top:8px">{label}</div>
            <div style="font-size:13px;margin-top:4px;opacity:.8">
                {len(result['matched'])} of {len(result['jd_total'])} keywords matched
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"size": 32}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#6366F1"},
                "steps": [
                    {"range": [0,  40], "color": "#FEE2E2"},
                    {"range": [40, 70], "color": "#FEF3C7"},
                    {"range": [70,100], "color": "#D1FAE5"},
                ],
                "threshold": {
                    "line": {"color": "#6366F1", "width": 3},
                    "thickness": 0.8,
                    "value": score,
                },
            },
            title={"text": "ATS Match Score"},
        ))
        fig.update_layout(height=300, margin=dict(t=40, b=10, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**✅ Matched Keywords**")
            chips = " ".join(
                f'<span class="skill-chip chip-match">{s}</span>'
                for s in sorted(result["matched"])
            )
            st.markdown(chips or "_None matched_", unsafe_allow_html=True)

        with col_b:
            st.markdown("**❌ Missing Keywords**")
            chips = " ".join(
                f'<span class="skill-chip chip-missing">{s}</span>'
                for s in sorted(result["missing"])
            )
            st.markdown(chips or "_No gaps found!_", unsafe_allow_html=True)

        st.divider()

        # Pie chart
        fig2 = px.pie(
            names=["Matched", "Missing"],
            values=[len(result["matched"]), len(result["missing"])],
            color_discrete_sequence=["#6366F1", "#E5E7EB"],
            hole=0.45,
            title="Keyword Coverage",
        )
        fig2.update_traces(textinfo="percent+label")
        fig2.update_layout(height=300, margin=dict(t=40, b=10))
        st.plotly_chart(fig2, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════
# TAB 3 — Skill Gap Analysis
# ════════════════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.analysis_done:
        st.info("Run the analysis in Tab 1 first.")
    else:
        st.subheader("Skill Gap Analysis")

        gaps = st.session_state.gap_analysis
        if not gaps:
            st.success("🎉 No skill gaps found! Your resume matches the job description well.")
        else:
            st.markdown(f"Found **{len(gaps)} skills** to develop. Here's what to learn and where:")
            st.divider()

            for gap in gaps:
                skill    = gap.get("skill", "")
                resource = gap.get("resource_name", "")
                url      = gap.get("url", "#")
                priority = gap.get("priority", "Medium")
                p_class  = f"priority-{priority.lower()}"

                st.markdown(f"""
                <div class="gap-card">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <span style="font-weight:600;font-size:15px">{skill}</span>
                        <span class="{p_class}">{priority} priority</span>
                    </div>
                    <div style="margin-top:6px;font-size:13px;color:#6B7280">
                        📚 <a href="{url}" target="_blank">{resource}</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        st.subheader("✨ AI Resume Improver")
        st.caption("Paste weak bullet points — Gemini will rewrite them to be stronger and ATS-friendly.")

        bullets_input = st.text_area(
            "Your current bullet points",
            height=150,
            placeholder="• Worked on Python projects\n• Did data analysis\n• Helped with machine learning tasks",
        )

        if st.button("✨ Improve with AI", disabled=not bullets_input.strip()):
            with st.spinner("Rewriting bullet points..."):
                improved = improve_resume_bullets(bullets_input)
                st.session_state.improved_bullets = improved

        if st.session_state.improved_bullets:
            st.markdown("**Improved version:**")
            st.success(st.session_state.improved_bullets)


# ════════════════════════════════════════════════════════════════════════
# TAB 4 — Report
# ════════════════════════════════════════════════════════════════════════
with tab4:
    if not st.session_state.analysis_done:
        st.info("Run the analysis in Tab 1 first.")
    else:
        st.subheader("Download Your Analysis Report")
        st.markdown("Get a complete PDF report of your resume analysis to share with mentors or keep for reference.")

        col1, col2, col3 = st.columns(3)
        result = st.session_state.ats_result

        with col1:
            st.metric("ATS Score", f"{result['score']}%")
        with col2:
            st.metric("Matched Keywords", len(result["matched"]))
        with col3:
            st.metric("Skill Gaps", len(result["missing"]))

        st.divider()

        if st.button("📄 Generate PDF Report", use_container_width=True, type="primary"):
            with st.spinner("Generating report..."):
                pdf_bytes = generate_pdf_report(
                    ats_score=result["score"],
                    matched=list(result["matched"]),
                    missing=list(result["missing"]),
                    gap_analysis=st.session_state.gap_analysis or [],
                )
            st.download_button(
                label="⬇️ Download Report (PDF)",
                data=pdf_bytes,
                file_name="resume_analysis_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )




