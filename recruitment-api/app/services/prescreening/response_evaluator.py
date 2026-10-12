import json
import re
import logging
import math
from typing import Dict, List, Any, Optional
from app.ai.gemini_client import call_gemini_json
from app.services.blind_screening import redact_text_pii

logger = logging.getLogger(__name__)


def evaluate_local_hybrid_answer(
    question_text: str,
    question_type: str,
    scoring_criteria: str,
    expected_concepts: List[str],
    candidate_answer: str
) -> Dict[str, Any]:
    """
    Deterministically evaluates a single answer against expected concepts and response depth.
    """
    ans = (candidate_answer or "").strip()
    if not ans or len(ans) < 10:
        return {
            "score": 25.0,
            "feedback": "Answer provided was minimal or empty. Candidate did not provide substantive explanation.",
            "key_strengths": [],
            "missing_concepts": expected_concepts,
            "depth_label": "Minimal"
        }

    ans_lower = ans.lower()
    
    # Check concept coverage
    found_concepts = []
    missing_concepts = []
    for c in expected_concepts:
        if c.lower() in ans_lower:
            found_concepts.append(c)
        else:
            missing_concepts.append(c)

    coverage_ratio = len(found_concepts) / max(1, len(expected_concepts))
    
    # Check response length & structure
    words = ans.split()
    word_count_score = min(1.0, len(words) / 45.0)  # ~45+ words considered comprehensive
    
    # Calculate baseline score
    base_score = (0.65 * coverage_ratio + 0.35 * word_count_score) * 100.0
    final_score = max(30.0, min(95.0, round(base_score, 1)))

    if final_score >= 80:
        feedback = f"Strong and thorough response. Clearly addressed the question and covered key concepts: {', '.join(found_concepts[:3])}."
        depth_label = "Comprehensive"
    elif final_score >= 60:
        feedback = f"Competent answer covering core ideas ({', '.join(found_concepts[:2]) or 'basic approach'}), with room for deeper technical elaboration."
        depth_label = "Good"
    else:
        feedback = "Response touched upon the problem but lacked specific technical implementation details or expected terminology."
        depth_label = "Developing"

    return {
        "score": final_score,
        "feedback": feedback,
        "key_strengths": [f"Addressed {c}" for c in found_concepts[:4]],
        "missing_concepts": missing_concepts[:3],
        "depth_label": depth_label
    }


def evaluate_prescreening_responses(
    job_title: str,
    questions: List[Dict[str, Any]],
    candidate_answers: List[Dict[str, Any]],
    candidate_identifier: str = "Candidate",
    is_blind_mode: bool = False
) -> Dict[str, Any]:
    """
    Evaluates candidate pre-screening questionnaire responses.
    Produces per-question evaluation and overall weighted score.
    """
    evaluations = []
    total_weighted_score = 0.0
    total_weight = 0.0
    
    # Map answers by question_id or text
    ans_by_id = {}
    for a in candidate_answers:
        qid = a.get("question_id") or a.get("id")
        if qid is not None:
            ans_by_id[qid] = a.get("answer_text") or a.get("answer", "")
        elif a.get("question_text"):
            ans_by_id[a["question_text"]] = a.get("answer_text") or a.get("answer", "")

    for q in questions:
        qid = q.get("id") or q.get("question_id")
        qtext = q.get("question_text", "")
        qtype = q.get("question_type", "technical")
        criteria = q.get("scoring_criteria", "")
        weight = float(q.get("weight", 1.0))
        
        expected_raw = q.get("expected_concepts")
        expected_concepts = []
        if isinstance(expected_raw, list):
            expected_concepts = expected_raw
        elif isinstance(expected_raw, str):
            try:
                expected_concepts = json.loads(expected_raw)
            except Exception:
                expected_concepts = [c.strip() for c in expected_raw.split(",") if c.strip()]
        if not expected_concepts:
            expected_concepts = ["Architecture", "Implementation", "Best Practices"]

        # Retrieve candidate answer
        cand_ans = ans_by_id.get(qid) or ans_by_id.get(qtext) or ""
        
        eval_item = evaluate_local_hybrid_answer(
            question_text=qtext,
            question_type=qtype,
            scoring_criteria=criteria,
            expected_concepts=expected_concepts,
            candidate_answer=cand_ans
        )

        eval_record = {
            "question_id": qid,
            "question_text": qtext,
            "question_type": qtype,
            "scoring_criteria": criteria,
            "category": q.get("category", "Technical Skills"),
            "candidate_answer": cand_ans,
            "score": eval_item["score"],
            "feedback": eval_item["feedback"],
            "key_strengths": eval_item["key_strengths"],
            "missing_concepts": eval_item["missing_concepts"],
            "weight": weight,
            "is_required": q.get("is_required", True)
        }
        evaluations.append(eval_record)
        
        total_weighted_score += (eval_item["score"] * weight)
        total_weight += weight

    overall_score = round(total_weighted_score / max(0.1, total_weight), 1) if total_weight > 0 else 50.0
    overall_score = max(10.0, min(98.0, overall_score))

    if overall_score >= 80:
        overall_label = "Strong"
        summary = f"{candidate_identifier} demonstrated solid technical depth across pre-screening questions with comprehensive explanations."
    elif overall_score >= 60:
        overall_label = "Competent"
        summary = f"{candidate_identifier} provided good fundamental responses, demonstrating practical familiarity with the required stack."
    elif overall_score >= 40:
        overall_label = "Developing"
        summary = f"{candidate_identifier} answered the questions with basic conceptual awareness, but lacked detailed implementation specifics."
    else:
        overall_label = "Needs Review"
        summary = f"{candidate_identifier} provided minimal pre-screening answers requiring direct clarification during technical interview."

    # Collect strengths and gaps
    all_strengths = []
    all_gaps = []
    for ev in evaluations:
        all_strengths.extend(ev.get("key_strengths", []))
        all_gaps.extend(ev.get("missing_concepts", []))

    strengths_summary = f"Demonstrated competence in: {', '.join(list(set(all_strengths))[:4])}." if all_strengths else "Basic technical responses provided."
    gap_summary = f"Areas to probe in interview: {', '.join(list(set(all_gaps))[:4])}." if all_gaps else "No major technical conceptual gaps identified."

    # Attempt Gemini Deep Evaluation if configured
    prompt = f"""
You are an expert technical interviewer evaluating pre-screening answers for {candidate_identifier} applying for {job_title}.
Questions and Candidate Answers:
{json.dumps([{'question': e['question_text'], 'answer': e['candidate_answer'], 'criteria': e.get('scoring_criteria', '')} for e in evaluations])}

Provide a refined evaluation JSON with keys:
- "overall_score": float (0-100)
- "overall_label": "Strong" | "Competent" | "Developing" | "Needs Review"
- "summary": str
- "strengths_summary": str
- "gap_summary": str
- "evaluations": list of objects matching each question with "feedback", "key_strengths", "missing_concepts", "score"
"""
    try:
        gemini_res = call_gemini_json(prompt)
        if gemini_res and isinstance(gemini_res, dict) and "overall_score" in gemini_res and "summary" in gemini_res:
            g_score = float(gemini_res.get("overall_score", overall_score))
            g_label = gemini_res.get("overall_label", overall_label)
            g_summary = gemini_res.get("summary", summary)
            if not math.isfinite(g_score):
                raise ValueError("AI score must be finite")
            g_score = max(10.0, min(99.0, round(0.75 * overall_score + 0.25 * max(0, min(100, g_score)), 1)))
            g_label = "Strong" if g_score >= 80 else "Competent" if g_score >= 60 else "Developing" if g_score >= 40 else "Needs Review"
            if not isinstance(g_summary, str):
                raise ValueError("AI summary must be text")
            if is_blind_mode:
                g_summary = redact_text_pii(g_summary, candidate_id=None)
            
            return {
                "overall_score": max(10.0, min(99.0, g_score)),
                "overall_label": g_label,
                "summary": g_summary,
                "strengths_summary": gemini_res.get("strengths_summary", strengths_summary),
                "gap_summary": gemini_res.get("gap_summary", gap_summary),
                "evaluations": evaluations,
                "ai_source": "gemini_evaluator"
            }
    except Exception as e:
        logger.warning("Gemini evaluation error: %s", str(e))

    return {
        "overall_score": overall_score,
        "overall_label": overall_label,
        "summary": summary,
        "strengths_summary": strengths_summary,
        "gap_summary": gap_summary,
        "evaluations": evaluations,
        "ai_source": "hybrid_prescreening_engine"
    }
