"""
Document-type-aware field extraction from OCR output.

Input : OCR lines [{text, bbox, confidence}] in reading order, plus the predicted document type.
Output: {
  "fields": [{key, label, value, confidence}],   only fields that were actually found
  "table":  {"columns": [...], "rows": [[...]]}   grade / marks table for academic records
}

Everything here is rule based (regex + layout). Every value is copied from the OCR text,
nothing is inferred or filled in: a field that is not found is simply absent.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

INSTITUTION_WORDS = ["university", "institute", "college", "academy", "polytechnic", "school of", "school",
                     "nptel", "coursera", "udemy", "edx", "infosys", "springboard", "microsoft", "google",
                     "ibm", "tata consultancy", "wipro", "accenture", "zoho", "hcl", "ieee", "freshworks"]
TITLE_RX = re.compile(r"(certificate|diploma|grade\s*(sheet|card)|mark\s*sheet|statement\s+of\s+marks|transcript|"
                      r"letter\s+of\s+recommendation|recommendation\s+letter|to\s+whom\s+it\s+may\s+concern|bonafide|"
                      r"completion\s+letter|provisional)", re.I)
NAME_TOKEN = r"[A-Z][A-Za-z'\.]*"
NAME_RX = re.compile(rf"^(?:(?:Mr|Ms|Mrs|Dr|Prof)\.?\s+)?({NAME_TOKEN}(?:\s+{NAME_TOKEN}){{1,4}})$")
DATE_RX = re.compile(
    r"(\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{4}\b|"
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b|"
    r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b)", re.I)
REG_LABEL_RX = re.compile(r"(?:Register(?:ation)?\s*(?:Number|No\.?)|Reg\.?\s*No\.?|Roll\s*(?:Number|No\.?)|"
                          r"Enrol(?:l)?ment\s*(?:Number|No\.?)|Student\s*ID|USN|PRN)\s*[:\-\.]?\s*([A-Z0-9][A-Z0-9/\-]{3,})", re.I)
REG_BARE_RX = re.compile(r"\b(\d{2}[A-Z]{3}\d{4})\b")
CERT_NO_RX = re.compile(r"(?:Certificate\s*(?:No\.?|Number|ID)|Cert\.?\s*No\.?|Serial\s*No\.?|Credential\s*ID|"
                        r"Diploma\s*No\.?|Ref(?:erence)?\s*(?:No\.?)?)\s*[:\-\.]?\s*([A-Z0-9][A-Z0-9/\-]{3,})", re.I)
CGPA_RX = re.compile(r"\bC\.?\s*G\.?\s*P\.?\s*A\.?[^0-9]{0,40}?(\d{1,2}\.\d{1,2})", re.I)
GPA_RX = re.compile(r"\b(?:S\.?G\.?P\.?A|G\.?P\.?A)\b[^0-9]{0,10}(\d{1,2}\.\d{1,2})", re.I)
PERCENT_RX = re.compile(r"(?:Percentage|score\s+of|scored)?[^0-9]{0,15}?(\d{1,3}(?:\.\d{1,2})?)\s*%", re.I)
SEM_RX = re.compile(r"\b(?:Semester|Sem)\s*[:\-]?\s*((?:Fall|Winter|Summer)?\s*(?:Semester)?\s*[IVX0-9]+(?:\s*[-/]\s*\d{2,4})?)", re.I)
SEM_NAMED_RX = re.compile(r"\b((?:Fall|Winter|Summer)\s+Semester\s+\d{4}\s*-\s*\d{2,4})", re.I)
EXAM_RX = re.compile(r"Month\s*(?:&|and)\s*Year\s*of\s*(?:Examination|Exam)\s*[:\-]?\s*([A-Za-z]+\s+\d{4})", re.I)
DEGREE_RX = re.compile(r"((?:Bachelor|Master|Doctor)\s+of\s+[A-Za-z]+(?:\s+(?:in|of|and|&)\s+[A-Za-z &]+)?|"
                       r"\b(?:B\.?\s?Tech|M\.?\s?Tech|B\.?\s?E\.|B\.?\s?Sc|M\.?\s?Sc|MBA|MCA|BCA|B\.?\s?Com|Ph\.?\s?D)\b[^,\n]{0,60})")
ROLE_RX = re.compile(r"\b(Registrar|Vice[\s-]*Chancellor|Controller\s+of\s+Examinations|Dean(?:\s*[-:]?\s*Academics)?|"
                     r"Director|Principal|Head\s+of\s+(?:the\s+)?Department|Program(?:me)?\s+Coordinator|HR\s+Manager|"
                     r"Chief\s+Executive\s+Officer|Professor)\b", re.I)
COURSE_CODE_RX = re.compile(r"^[A-Z]{2,5}\s?\d{3,4}[A-Z]?$")
GRADE_RX = re.compile(r"^(?:O|S|A\+|A|B\+|B|C\+|C|D|E|F|P|U|AB|N)$")
INTRO_RX = re.compile(r"(certify\s+that(?:\s+(?:Mr|Ms|Mrs)\.?(?:/\s*Ms\.?)?)?|presented\s+to|awarded\s+to|conferred\s+(?:up)?on|"
                      r"hereby\s+certify\s+that|recommend(?:ation)?\s+(?:for\s+)?)\s*[:,]?\s*(.*)$", re.I)
STOP_NAME = {"this", "the", "has", "certificate", "university", "institute", "college", "certify", "date", "degree",
             "grade", "sheet", "name", "register", "number", "programme", "semester", "course", "total", "of"}


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" :.-,|")


def _valid_name(s: str) -> Optional[str]:
    s = _clean(s)
    s = re.sub(r"^(?:Mr|Ms|Mrs|Dr|Prof)\.?\s*(?:/\s*(?:Mr|Ms|Mrs)\.?)?\s*", "", s)
    m = NAME_RX.match(s)
    if not m:
        return None
    name = m.group(1)
    if any(w.lower().strip(".") in STOP_NAME for w in name.split()):
        return None
    return name


def group_rows(lines: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Group OCR boxes into visual rows (vertical centre overlap), each row sorted left to right."""
    rows: List[List[Dict[str, Any]]] = []
    for l in sorted(lines, key=lambda l: (l["bbox"][1] + l["bbox"][3]) / 2):
        cy = (l["bbox"][1] + l["bbox"][3]) / 2
        h = max(1, l["bbox"][3] - l["bbox"][1])
        if rows:
            last = rows[-1]
            lcy = sum((x["bbox"][1] + x["bbox"][3]) / 2 for x in last) / len(last)
            if abs(cy - lcy) < 0.55 * h:
                last.append(l)
                continue
        rows.append([l])
    return [sorted(r, key=lambda l: l["bbox"][0]) for r in rows]


class FieldExtractor:
    def extract(self, lines: List[Dict[str, Any]], doc_type: str) -> Dict[str, Any]:
        rows = group_rows(lines)
        row_texts = [(" ".join(c["text"] for c in r), min(c["confidence"] for c in r)) for r in rows]
        text = "\n".join(t for t, _ in row_texts)
        found: Dict[str, Tuple[str, float]] = {}

        def put(key, value, conf=0.9):
            if value and key not in found:
                found[key] = (_clean(value), round(float(conf), 3))

        def search(rx, key, group=1):
            for t, c in row_texts:
                m = rx.search(t)
                if m:
                    put(key, m.group(group), c)
                    return

        # document title and issuing institution (topmost matching rows)
        for t, c in row_texts[:12]:
            if TITLE_RX.search(t) and len(t) < 90:
                put("document_title", t, c)
                break
        for t, c in row_texts[:10]:
            low = t.lower()
            if any(w in low for w in INSTITUTION_WORDS) and len(t) < 90 and not TITLE_RX.search(t):
                put("institution", re.sub(r"^[A-Z]{2,4}\s+(?=[A-Z][a-z])", "", t), c)
                break

        # holder name: labelled field, then "certify that <name>" on the same or next row
        for t, c in row_texts:
            m = re.search(r"(?:Name\s*of\s*the\s*(?:Student|Candidate)|(?:the\s*)?Student(?:\s*Name)?|Candidate\s*Name|^Name)\s*[:\-]\s*(.+)", t, re.I)
            if m:
                cut = re.split(r"\s{2,}|\||Register|Reg\.|Roll|Programme|Semester|Date", m.group(1))[0]
                n = _valid_name(cut)
                if n:
                    put("holder_name", n, c)
                    break
        if "holder_name" not in found:
            for i, (t, c) in enumerate(row_texts):
                m = INTRO_RX.search(t)
                if not m:
                    continue
                tail = re.split(r"\s+(?:has|who|is|for|of|\()\b", m.group(2))[0]
                n = _valid_name(tail) if tail else None
                if not n and i + 1 < len(row_texts):
                    nxt = re.split(r"\s+(?:has|who|is|\()\b", row_texts[i + 1][0])[0]
                    n = _valid_name(nxt)
                    c = row_texts[i + 1][1]
                if n:
                    put("holder_name", n, c)
                    break

        search(REG_LABEL_RX, "register_number")
        search(REG_BARE_RX, "register_number")
        search(CERT_NO_RX, "certificate_number")

        # programme / degree
        for t, c in row_texts:
            m = re.search(r"Program(?:me)?\s*[:\-]\s*(.+)", t, re.I)
            if m:
                put("programme", re.split(r"\s{2,}|Semester", m.group(1))[0], c)
                break
        search(DEGREE_RX, "programme")

        # course title for completion style certificates
        for i, (t, c) in enumerate(row_texts):
            if re.search(r"completed\s+(?:the\s+)?(?:course|program|programme)\s*$", t, re.I) and i + 1 < len(row_texts):
                put("course", row_texts[i + 1][0], row_texts[i + 1][1])
                break
            m = re.search(r"(?:completed\s+(?:the\s+)?(?:course|program)|course\s+(?:on|titled))\s+[\"']?(.{4,70})", t, re.I)
            if m:
                put("course", m.group(1), c)
                break
        m = re.search(r"(?:internship\s+as|participated\s+in(?:\s+the)?|Place\s+in)\s+(.{4,70}?)(?:\s+(?:at|organi[sz]ed|held|from)\b|$)", text, re.I | re.M)
        if m:
            put("achievement", m.group(1))

        search(CGPA_RX, "cgpa")
        search(GPA_RX, "gpa")
        m = PERCENT_RX.search(text)
        if m:
            put("percentage", m.group(1) + "%")
        search(SEM_NAMED_RX, "semester")
        search(SEM_RX, "semester")
        search(EXAM_RX, "exam_session")
        m = re.search(r"(?:with|secured|Grade)\s*[:\-]?\s*(First\s+Class(?:\s+with\s+Distinction)?|Second\s+Class|Distinction|"
                      r"Grade\s+[A-Z][+]?(?![A-Za-z])|\b[A-Z][+]?\s+Grade)", text)
        if m:
            put("class_awarded", m.group(1))

        # dates: explicit issue date first, else the first date on the page
        for t, c in row_texts:
            m = re.search(r"(?:Date\s*of\s*Issue|Issued\s*on|Dated?)\s*[:\-]?\s*(.+)", t, re.I)
            if m:
                d = DATE_RX.search(m.group(1))
                if d:
                    put("issue_date", d.group(1), c)
                    break
        if "issue_date" not in found:
            search(DATE_RX, "date")

        roles = []
        for t, _ in row_texts[len(row_texts) // 2:]:
            for m in ROLE_RX.finditer(t):
                r = _clean(m.group(1))
                if r.lower() not in [x.lower() for x in roles]:
                    roles.append(r)
        if roles:
            put("signatories", ", ".join(roles[:3]))

        table = self._table(rows) if doc_type == "ACADEMIC_RECORD" else None
        if table and table["rows"]:
            put("courses_listed", str(len(table["rows"])))

        order = ["document_title", "holder_name", "register_number", "institution", "programme", "course",
                 "achievement", "semester", "exam_session", "cgpa", "gpa", "percentage", "class_awarded",
                 "courses_listed", "certificate_number", "issue_date", "date", "signatories"]
        labels = {"document_title": "Document title", "holder_name": "Name", "register_number": "Register number",
                  "institution": "Issuing institution", "programme": "Programme / degree", "course": "Course",
                  "achievement": "Event / role", "semester": "Semester", "exam_session": "Exam session",
                  "cgpa": "CGPA", "gpa": "GPA / SGPA", "percentage": "Percentage", "class_awarded": "Class / grade",
                  "courses_listed": "Courses listed", "certificate_number": "Certificate / ref number",
                  "issue_date": "Date of issue", "date": "Date", "signatories": "Signed by"}
        fields = [{"key": k, "label": labels[k], "value": found[k][0], "confidence": found[k][1]}
                  for k in order if k in found]
        return {"fields": fields, "table": table}

    def _table(self, rows: List[List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        """Pull course rows: rows holding a course code or subject + grade/marks cells."""
        out = []
        for r in rows:
            cells = [c["text"].strip() for c in r if c["text"].strip()]
            if len(cells) < 3:
                continue
            code_i = next((i for i, c in enumerate(cells) if COURSE_CODE_RX.match(c.replace(" ", ""))), None)
            if code_i is not None:
                rest = cells[code_i + 1:]
                title = next((c for c in rest if re.search(r"[A-Za-z]{3,}", c) and not GRADE_RX.match(c)), "")
                credits = next((c for c in rest if re.fullmatch(r"\d(?:\.\d)?", c)), "")
                grade = next((c for c in rest if GRADE_RX.match(c)), "")
                out.append({"code": cells[code_i], "title": title, "credits": credits, "grade": grade})
                continue
            nums = [c for c in cells if re.fullmatch(r"\d{1,3}", c)]
            words = [c for c in cells if re.search(r"[A-Za-z]{4,}", c) and c.upper() not in ("PASS", "FAIL")]
            result = next((c for c in cells if c.upper() in ("PASS", "FAIL")), "")
            if words and len(nums) >= 2 and result:
                out.append({"code": "", "title": words[0], "credits": "", "grade": f"{nums[-1]}/{nums[-2]} {result}"})
        if not out:
            return None
        return {"columns": ["Code", "Course title", "Credits", "Grade / marks"],
                "rows": [[o["code"], o["title"], o["credits"], o["grade"]] for o in out]}
