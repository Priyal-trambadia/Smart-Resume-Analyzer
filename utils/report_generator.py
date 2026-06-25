from fpdf import FPDF
from datetime import date


def clean_text(text):
    """
    Replace Unicode characters unsupported by Helvetica.
    """
    if not text:
        return ""

    replacements = {
        "✓": "[OK]",
        "✗": "[X]",
        "•": "|",
        "—": "-",
        "–": "-",
        "→": "->",
        "“": '"',
        "”": '"',
        "'": "'",
        "'": "'",
        "₹": "Rs.",
    }

    text = str(text)

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


class ResumeReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(99, 102, 241)
        self.cell(0, 12, "AI Resume Analysis Report", align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 10)
        self.set_text_color(107, 114, 128)
        self.cell(
            0,
            6,
            f"Generated on {date.today().strftime('%B %d, %Y')}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        self.ln(4)
        self.set_draw_color(229, 231, 235)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(156, 163, 175)
        self.cell(
            0,
            10,
            f"Page {self.page_no()} | AI Resume Analyzer",
            align="C",
        )

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(31, 41, 55)
        self.set_fill_color(243, 244, 246)
        self.cell(
            0,
            10,
            clean_text(title),
            fill=True,
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(2)

    def body_text(self, text, color=(55, 65, 81)):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*color)
        self.multi_cell(0, 6, clean_text(text))
        self.ln(1)

    def colored_score(self, score):
        if score >= 70:
            color = (5, 150, 105)
            label = "Strong Match"
        elif score >= 40:
            color = (217, 119, 6)
            label = "Partial Match"
        else:
            color = (220, 38, 38)
            label = "Weak Match"

        self.set_font("Helvetica", "B", 36)
        self.set_text_color(*color)
        self.cell(
            0,
            16,
            f"{score}% - {label}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(4)

    def keyword_list(self, keywords, color=(55, 65, 81)):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*color)

        row = []

        for kw in sorted(keywords):
            row.append(clean_text(kw))

            if len(row) == 4:
                self.cell(
                    0,
                    6,
                    " | ".join(row),
                    new_x="LMARGIN",
                    new_y="NEXT",
                )
                row = []

        if row:
            self.cell(
                0,
                6,
                " | ".join(row),
                new_x="LMARGIN",
                new_y="NEXT",
            )

        self.ln(2)


def generate_pdf_report(
    ats_score,
    matched,
    missing,
    gap_analysis,
):
    pdf = ResumeReport()
    pdf.add_page()

    # ATS Score
    pdf.section_title("ATS Score")
    pdf.colored_score(ats_score)

    pdf.body_text(
        f"Your resume matched {len(matched)} out of "
        f"{len(matched) + len(missing)} keywords found in the job description."
    )

    pdf.ln(4)

    # Matched Keywords
    pdf.section_title(f"[OK] Matched Keywords ({len(matched)})")

    if matched:
        pdf.keyword_list(matched, color=(5, 150, 105))
    else:
        pdf.body_text("No keywords matched.")

    pdf.ln(4)

    # Missing Keywords
    pdf.section_title(f"[X] Missing Keywords ({len(missing)})")

    if missing:
        pdf.keyword_list(missing, color=(220, 38, 38))
    else:
        pdf.body_text("No missing keywords - great match!")

    pdf.ln(4)

    # Skill Gap Analysis
    if gap_analysis:
        pdf.add_page()

        pdf.section_title("Skill Gap Analysis & Learning Resources")
        pdf.ln(2)

        for gap in gap_analysis:
            skill = clean_text(gap.get("skill", ""))
            resource = clean_text(gap.get("resource_name", ""))
            url = clean_text(gap.get("url", ""))
            priority = gap.get("priority", "Medium")

            priority_colors = {
                "High": (220, 38, 38),
                "Medium": (217, 119, 6),
                "Low": (5, 150, 105),
            }

            p_color = priority_colors.get(priority, (107, 114, 128))

            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(31, 41, 55)
            pdf.cell(140, 7, skill)

            pdf.set_text_color(*p_color)
            pdf.cell(
                0,
                7,
                f"[{priority}]",
                new_x="LMARGIN",
                new_y="NEXT",
            )

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(99, 102, 241)
            pdf.multi_cell(
                0,
                6,
                clean_text(f"{resource} - {url}")
            )

            pdf.ln(2)

    # Tips
    pdf.ln(4)

    pdf.section_title("Quick Tips to Improve Your ATS Score")

    tips = [
        "1. Add missing keywords naturally in your skills section and experience bullets.",
        "2. Use exact phrases from the job description (ATS matches exact strings).",
        "3. Avoid tables, columns, and images - ATS parsers prefer plain text.",
        "4. Include both long form and abbreviations: Machine Learning (ML).",
        "5. Tailor your resume for each application - do not use one generic resume.",
    ]

    for tip in tips:
        pdf.body_text(tip)

    return bytes(pdf.output())