# start.py
from flask import Flask, render_template, request
import apif
import re

app = Flask(__name__)

UPLOADED_IMAGE_PATH = "/mnt/data/7cb3ca64-a03e-4648-abb3-2682f2a4e95a.png"


def fix_latex(text: str) -> str:
    """
    Clean up escaped LaTeX so MathJax can render it.
    """
    text = text or ""
    text = text.replace("\\\\frac", "\\frac")
    text = text.replace("\\\\sqrt", "\\sqrt")
    text = re.sub(r"\\\\([a-zA-Z])", r"\\\1", text)
    text = text.replace("\\\\", "\\")
    return text


# ---------- PARSER ----------
def parse_mcq_text(text: str):
    """
    Parse Gemini text into a list of MCQs:
    {
      "question": str,
      "options": {"A":str,"B":str,"C":str,"D":str},
      "answer": "A",
      "explanation": "..."
    }
    """
    if not text:
        return []

    lines = text.splitlines()
    items = []
    current = None

    # helper: if option text accidentally contains explanation-like stuff,
    # split it out and append to current["explanation"]
    def clean_option_and_maybe_extract_expl(opt_text: str) -> str:
        nonlocal current

        # keywords that usually indicate explanation / self-talk
        keywords = [
            "Explanation:", "This is simple", "This is straightforward",
            "Wait,", "Wait ", "Let me", "So option", "Hence option",
            "Therefore option", "is correct", "Correct answer is"
        ]

        for kw in keywords:
            idx = opt_text.find(kw)
            if idx != -1:
                # split into pure option + explanation tail
                pure = opt_text[:idx].strip()
                expl_part = opt_text[idx:].strip()

                # remove leading "Explanation:" if present
                if expl_part.lower().startswith("explanation:"):
                    expl_part = expl_part[len("Explanation:"):].strip()

                if expl_part:
                    if current.get("explanation"):
                        current["explanation"] += " " + expl_part
                    else:
                        current["explanation"] = expl_part
                return pure

        return opt_text

    def flush():
        """
        Save current question if it looks like a real MCQ.
        Drop intro lines that have no options and no answer.
        """
        nonlocal current
        if not current:
            return

        opts = current.get("options", {})
        # number of non-empty options
        num_non_empty_opts = sum(1 for v in opts.values() if v.strip())
        has_answer = (current.get("answer") or "").strip() in ["A", "B", "C", "D"]

        # If it looks like just an intro/heading (no options & no answer), ignore it
        if num_non_empty_opts < 2 and not has_answer:
            current = None
            return

        # Ensure all four option keys exist
        for k in ["A", "B", "C", "D"]:
            opts.setdefault(k, "")

        items.append({
            "question": (current.get("question") or "").strip(),
            "options": opts,
            "answer": (current.get("answer") or "").strip(),
            "explanation": (current.get("explanation") or "").strip()
        })
        current = None

    mode = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue

        s = line.strip()

        # 1) Question start like "1. ..." or "Q1: ..."
        if re.match(r'^\d+\s*[\.\)]\s*', s) or re.match(r'^[Qq]\d+[:\-]\s*', s):
            flush()
            qtext = re.sub(r'^\d+\s*[\.\)]\s*', '', s)
            qtext = re.sub(r'^[Qq]\d+[:\-]\s*', '', qtext).strip()
            current = {
                "question": qtext,
                "options": {},
                "answer": None,
                "explanation": None
            }
            mode = "question"
            continue

        # If nothing yet, start a question with this line
        if current is None:
            current = {"question": s, "options": {}, "answer": None, "explanation": None}
            mode = "question"
            continue

        # 2) ANSWER line  (check BEFORE options so "Answer: A" is not read as option A)
        m_ans = re.match(
            r'^(?:Answer|Ans|Correct answer|Correct)\s*[:\-]?\s*([A-D])',
            s, flags=re.I
        )
        if m_ans:
            current["answer"] = m_ans.group(1).upper()
            mode = "answer"
            continue

        # 3) EXPLANATION line
        m_exp = re.match(
            r'^(?:Explanation|Reason|Solution)\s*[:\-]?\s*(.*)',
            s, flags=re.I
        )
        if m_exp:
            extra = m_exp.group(1).strip()
            if current.get("explanation"):
                current["explanation"] += " " + extra
            else:
                current["explanation"] = extra
            mode = "explanation"
            continue

        # 4) OPTION lines: A) / A. / A -
        m_opt = re.match(r'^([A-D])\s*[\)\.\-:]?\s*(.*)', s, flags=re.I)
        if m_opt:
            key = m_opt.group(1).upper()
            opt_text = m_opt.group(2).strip()

            # 🔥 clean off any explanation-like tail from the option text
            opt_text = clean_option_and_maybe_extract_expl(opt_text)

            current["options"][key] = opt_text
            mode = "options"
            continue

        # 5) Continuation / fallback
        if mode == "question":
            current["question"] += " " + s
        elif mode == "options":
            if current["options"]:
                last_key = sorted(current["options"].keys())[-1]
                extra = clean_option_and_maybe_extract_expl(s)
                current["options"][last_key] = (
                    current["options"][last_key] + " " + extra
                )
            else:
                current["question"] += " " + s
        elif mode == "explanation":
            if current.get("explanation"):
                current["explanation"] += " " + s
            else:
                current["explanation"] = s
        else:
            current["question"] += " " + s

    # flush last question
    flush()
    return items


# ---------- FLASK ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html", uploaded_image=UPLOADED_IMAGE_PATH)


@app.route("/generate", methods=["POST"])
def generate():
    topic = request.form.get("topic", "").strip()
    num_q = request.form.get("num_questions", "1")
    enable_timer = request.form.get("enable_timer")
    minutes_per_question = request.form.get("minutes_per_question", "1")

    if not topic:
        return "Please enter a topic", 400

    try:
        num_q = int(num_q)
    except Exception:
        num_q = 1

    try:
        minutes_per_question = int(minutes_per_question)
    except Exception:
        minutes_per_question = 1

    # 1) call Gemini
    raw = apif.generate_mcq(topic, num_q)

    # 2) clean LaTeX escapes
    raw = fix_latex(raw)

    # 3) parse to structured MCQs
    questions = parse_mcq_text(raw)

    # 4) fallback: show raw output page if parsing failed
    if not questions:
        return render_template("output.html", result=raw)

    # 5) render quiz
    return render_template(
        "quiz.html",
        questions=questions,
        enable_timer=bool(enable_timer),
        minutes_per_question=minutes_per_question,
        topic=topic
    )


if __name__ == "__main__":
    app.run(debug=True)
