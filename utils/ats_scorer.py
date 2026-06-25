
# utils/ats_scorer.py

def compute_ats_score(resume_skills, jd_keywords):
    """
    Compare resume skills with job description keywords
    and calculate ATS score.

    Returns:
    {
        "score": int,
        "matched": set,
        "missing": set,
        "jd_total": set
    }
    """

    # Clean and normalize
    resume_set = {
        str(skill).lower().strip()
        for skill in resume_skills
        if skill and str(skill).strip()
    }

    jd_set = {
        str(skill).lower().strip()
        for skill in jd_keywords
        if skill and str(skill).strip()
    }

    # No JD keywords
    if not jd_set:
        return {
            "score": 0,
            "matched": set(),
            "missing": set(),
            "jd_total": set(),
        }

    # Exact matches only
    matched = resume_set.intersection(jd_set)

    # Missing skills
    missing = jd_set - matched

    # ATS Score
    score = round(
        (len(matched) / len(jd_set)) * 100
    )

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "jd_total": jd_set,
    }












# def compute_ats_score(resume_skills: list[str], jd_keywords: list[str]) -> dict:
#     """
#     Compare resume skills vs JD keywords and compute an ATS match score.

#     Returns a dict:
#     {
#         "score": int (0-100),
#         "matched": set of matched keywords,
#         "missing": set of missing keywords,
#         "jd_total": set of all JD keywords,
#     }
#     """
#     # Normalise to lowercase for comparison
#     resume_set = set(s.lower().strip() for s in resume_skills if s)
#     jd_set     = set(k.lower().strip() for k in jd_keywords  if k)

#     if not jd_set:
#         return {"score": 0, "matched": set(), "missing": set(), "jd_total": set()}

#     # Fuzzy-ish matching: a JD keyword is "matched" if it appears anywhere
#     # in the resume skill list (handles "Machine Learning" vs "ML" partially)
#     matched = set()
#     missing = set()

#     for jd_kw in jd_set:
#         # Exact match
#         if jd_kw in resume_set:
#             matched.add(jd_kw)
#             continue
#         # Partial match: jd keyword is a substring of any resume skill or vice versa
#         found = any(
#             jd_kw in r_skill or r_skill in jd_kw
#             for r_skill in resume_set
#         )
#         if found:
#             matched.add(jd_kw)
#         else:
#             missing.add(jd_kw)

#     score = round(len(matched) / len(jd_set) * 100)

#     return {
#         "score":    score,
#         "matched":  matched,
#         "missing":  missing,
#         "jd_total": jd_set,
#     }
