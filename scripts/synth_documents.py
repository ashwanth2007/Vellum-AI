"""
Synthetic document renderers used to build the document-type classifier dataset.

Each generator returns (PIL.Image RGB, text) where text is the ground-truth string
content of the page. Classes produced here:
  CERTIFICATE      -> gen_certificate()
  ACADEMIC_RECORD  -> gen_grade_sheet(), gen_completion_letter(), render_lor()
  OTHER_DOCUMENT   -> gen_other_document()
Plus phone_photo() / scan_effect() augmentations shared by all document classes.
"""

import math
import random
import string
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

try:
    from faker import Faker
    _FAKE = Faker(["en_IN", "en_US"])
except Exception:  # faker is optional, fall back to static pools
    _FAKE = None

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype"), Path("/Library/Fonts")]

SERIF = ["georgia.ttf", "times.ttf", "cambria.ttc", "BOOKOS.TTF", "constan.ttf", "pala.ttf", "GARA.TTF"]
SERIF_BOLD = ["georgiab.ttf", "timesbd.ttf", "cambriab.ttf", "BOOKOSB.TTF", "constanb.ttf", "palab.ttf"]
SANS = ["arial.ttf", "calibri.ttf", "segoeui.ttf", "verdana.ttf", "tahoma.ttf", "corbel.ttf", "Candara.ttf"]
SANS_BOLD = ["arialbd.ttf", "calibrib.ttf", "segoeuib.ttf", "verdanab.ttf", "tahomabd.ttf", "corbelb.ttf"]
SCRIPT = ["Gabriola.ttf", "georgiai.ttf", "timesi.ttf", "BOOKOSI.TTF", "cambriai.ttf", "segoesc.ttf", "Inkfree.ttf"]
MONO = ["consola.ttf", "cour.ttf"]

_font_cache = {}


def _find(name: str) -> Optional[str]:
    for d in FONT_DIRS:
        p = d / name
        if p.exists():
            return str(p)
    return None


def font(pool: List[str], size: int, rng: random.Random) -> ImageFont.FreeTypeFont:
    candidates = [f for f in pool if _find(f)]
    name = rng.choice(candidates) if candidates else None
    key = (name, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(_find(name), size) if name else ImageFont.load_default()
    return _font_cache[key]


# ----------------------------------------------------------------------------- pools
FIRST = ["Arun", "Priya", "Aditya", "Sneha", "Rahul", "Ananya", "Vikram", "Kavya", "Rohan", "Deepika",
         "Nikhil", "Meera", "Karthik", "Divya", "Harish", "Lakshmi", "Sanjay", "Pooja", "Varun", "Nandhini",
         "Arjun", "Ishita", "Siddharth", "Aishwarya", "Manoj", "Keerthana", "Abishek", "Swetha", "Gokul", "Riya",
         "John", "Emily", "Michael", "Sarah", "David", "Fatima", "Mohammed", "Aisha", "Daniel", "Grace"]
LAST = ["Kumar", "Sharma", "Verma", "Patel", "Deshmukh", "Sundaram", "Malhotra", "Reddy", "Gupta", "Joshi",
        "Nair", "Iyer", "Krishnan", "Raman", "Subramanian", "Menon", "Rao", "Pillai", "Singh", "Chatterjee",
        "Smith", "Johnson", "Williams", "Brown", "Khan", "Ali", "Fernandes", "Das", "Bose", "Mehta"]
INSTITUTIONS = [
    "Apex University of Technology", "Global Institute of Science and Engineering",
    "National Institute of Higher Studies", "Metropolitan University of Computing",
    "Southern Institute of Technology", "Pacific Coast University", "Coromandel College of Engineering",
    "Western Ghats University", "Indian Institute of Applied Sciences", "Deccan Technological University",
    "St. Joseph's College of Arts and Science", "Horizon Business School", "Kaveri Institute of Technology",
    "Lakeside Polytechnic College", "Northern Plains University", "Vellore Institute of Engineering Studies",
    "Royal Academy of Management", "Sunrise Institute of Information Technology",
]
DEGREES = [
    "Bachelor of Technology in Computer Science and Engineering", "Bachelor of Science in Information Technology",
    "Master of Science in Artificial Intelligence", "Master of Business Administration",
    "Bachelor of Engineering in Electronics and Communication", "Bachelor of Commerce",
    "Master of Technology in Data Science", "Bachelor of Arts in Economics", "Doctor of Philosophy in Physics",
    "Bachelor of Technology in Mechanical Engineering", "Master of Computer Applications",
]
DEGREE_SHORT = {"Bachelor of Technology": "B.Tech", "Bachelor of Science": "B.Sc", "Master of Science": "M.Sc",
                "Master of Business Administration": "MBA", "Bachelor of Engineering": "B.E.",
                "Bachelor of Commerce": "B.Com", "Master of Technology": "M.Tech", "Bachelor of Arts": "B.A.",
                "Doctor of Philosophy": "Ph.D", "Master of Computer Applications": "MCA"}
COURSES = [
    "Machine Learning Foundations", "Python for Data Science", "Deep Learning Specialization",
    "Cloud Computing Essentials", "Full Stack Web Development", "Introduction to Artificial Intelligence",
    "Data Structures and Algorithms", "Cyber Security Fundamentals", "Digital Marketing",
    "Internet of Things", "Natural Language Processing", "Blockchain Basics", "Computer Vision with PyTorch",
    "Project Management Professional", "Big Data Analytics", "Embedded Systems Design",
]
ORGS = ["Infosys Springboard", "NPTEL", "Coursera", "Tata Consultancy Services", "Zoho Corporation",
        "Wipro Technologies", "IBM SkillsBuild", "Google Developer Student Clubs", "IEEE Student Branch",
        "Microsoft Learn", "Freshworks", "L&T Technology Services", "Accenture", "HCL Tech"]
CERT_TITLES = [
    ("CERTIFICATE OF COMPLETION", "completion"), ("Certificate of Achievement", "achievement"),
    ("DEGREE CERTIFICATE", "degree"), ("Certificate of Participation", "participation"),
    ("INTERNSHIP CERTIFICATE", "internship"), ("Certificate of Excellence", "achievement"),
    ("Certificate of Merit", "achievement"), ("Course Completion Certificate", "completion"),
    ("PROVISIONAL CERTIFICATE", "degree"), ("Certificate of Appreciation", "participation"),
    ("DIPLOMA", "degree"), ("Certificate", "completion"),
]
SUBJECTS = [
    ("Engineering Mathematics", 4), ("Data Structures", 4), ("Operating Systems", 3), ("Computer Networks", 3),
    ("Database Management Systems", 4), ("Artificial Intelligence", 3), ("Compiler Design", 3),
    ("Software Engineering", 3), ("Theory of Computation", 3), ("Digital Logic Design", 4),
    ("Object Oriented Programming", 3), ("Discrete Mathematics", 4), ("Machine Learning", 3),
    ("Computer Architecture", 3), ("Probability and Statistics", 4), ("Technical English", 2),
    ("Environmental Studies", 2), ("Indian Constitution", 1), ("Cloud Architecture Design", 3),
    ("Physics for Engineers", 4), ("Chemistry", 3), ("Microprocessors", 3), ("Design and Analysis of Algorithms", 4),
    ("Web Technologies", 3), ("Cryptography", 3), ("Economics for Engineers", 2), ("Mini Project", 2),
]
GRADES = [("S", 10), ("A", 9), ("B", 8), ("C", 7), ("D", 6), ("E", 5), ("O", 10), ("A+", 9), ("B+", 7)]
PROG_CODES = ["BCE", "BIT", "MIS", "BEC", "BME", "MCA", "BCB", "BAI", "MDS"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
PALETTES = [
    ((250, 246, 234), (120, 20, 30), (30, 30, 60)),     # cream, maroon, navy
    ((255, 255, 255), (20, 60, 130), (20, 20, 20)),     # white, blue
    ((245, 250, 245), (20, 100, 60), (20, 40, 30)),     # mint, green
    ((252, 249, 240), (160, 120, 30), (40, 30, 20)),    # ivory, gold
    ((255, 255, 255), (90, 20, 110), (30, 20, 40)),     # white, purple
    ((244, 247, 252), (10, 90, 140), (15, 30, 50)),     # pale blue
    ((255, 253, 248), (200, 80, 20), (40, 30, 30)),     # orange
]


def name(rng):
    return f"{rng.choice(FIRST)} {rng.choice(LAST)}" if rng.random() < 0.8 else \
        f"{rng.choice(FIRST)} {rng.choice(string.ascii_uppercase)}. {rng.choice(LAST)}"


def date_str(rng, year=None):
    y = year or rng.randint(2016, 2026)
    d, m = rng.randint(1, 28), rng.randint(1, 12)
    fmt = rng.randint(0, 3)
    if fmt == 0:
        return f"{d:02d}/{m:02d}/{y}"
    if fmt == 1:
        return f"{d} {MONTHS[m - 1]} {y}"
    if fmt == 2:
        return f"{MONTHS[m - 1]} {d}, {y}"
    return f"{d:02d}-{m:02d}-{y}"


def reg_no(rng):
    s = rng.randint(0, 2)
    if s == 0:
        return f"{rng.randint(18, 26)}{rng.choice(PROG_CODES)}{rng.randint(1000, 9999)}"
    if s == 1:
        return f"{rng.randint(1000000, 9999999)}"
    return f"REG{rng.randint(100000, 999999)}"


def sentence(rng, n=12):
    if _FAKE is not None:
        _FAKE.seed_instance(rng.randint(0, 10 ** 9))
        return _FAKE.sentence(nb_words=n)
    words = ["the", "report", "project", "system", "market", "company", "quarter", "results", "team",
             "customer", "service", "growth", "plan", "data", "review", "meeting", "budget", "policy"]
    return " ".join(rng.choice(words) for _ in range(n)).capitalize() + "."


def paragraph(rng, n=5):
    return " ".join(sentence(rng, rng.randint(8, 16)) for _ in range(n))


# ----------------------------------------------------------------------------- drawing helpers
def text_center(draw, cx, y, txt, fnt, fill):
    w = draw.textlength(txt, font=fnt)
    draw.text((cx - w / 2, y), txt, font=fnt, fill=fill)
    return fnt.size


def wrap(draw, txt, fnt, max_w):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def signature(draw, x, y, w, h, rng, color=(20, 30, 90)):
    pts, cx, cy = [], x, y + h / 2
    for _ in range(rng.randint(10, 18)):
        cx += w / 14 + rng.uniform(-3, 5)
        cy = y + h / 2 + rng.uniform(-h * 0.45, h * 0.45)
        pts.append((cx, cy))
    draw.line(pts, fill=color, width=rng.randint(2, 3), joint="curve")
    if rng.random() < 0.6:
        lx = x + w * rng.uniform(0.2, 0.7)
        draw.arc([lx - 15, y + h * 0.2, lx + 20, y + h * 0.9], 0, 300, fill=color, width=2)


def seal(img, cx, cy, r, rng, color=(170, 25, 35), label="OFFICIAL SEAL"):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = rng.randint(150, 220)
    col = color + (a,)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=4)
    d.ellipse([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], outline=col, width=2)
    f = font(SANS_BOLD, max(10, r // 5), rng)
    n = len(label)
    for i, ch in enumerate(label):
        ang = math.pi * (1.1 + 0.8 * i / max(1, n - 1))
        tx, ty = cx + (r - 22) * math.cos(ang), cy + (r - 22) * math.sin(ang)
        d.text((tx - 5, ty - 6), ch, font=f, fill=col)
    star = [(cx + (r * 0.35 if k % 2 == 0 else r * 0.15) * math.cos(math.pi / 2 + k * math.pi / 5),
             cy - (r * 0.35 if k % 2 == 0 else r * 0.15) * math.sin(math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    d.polygon(star, fill=col)
    if rng.random() < 0.5:
        layer = layer.rotate(rng.uniform(-25, 25), center=(cx, cy))
    base = img.convert("RGBA")
    base.alpha_composite(layer)
    return base.convert("RGB")


def logo(draw, cx, cy, r, initials, rng, color):
    kind = rng.randint(0, 2)
    if kind == 0:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=4)
    elif kind == 1:
        draw.polygon([(cx, cy - r), (cx + r, cy - r * 0.4), (cx + r * 0.8, cy + r), (cx - r * 0.8, cy + r),
                      (cx - r, cy - r * 0.4)], outline=color, width=4)
    else:
        draw.rectangle([cx - r, cy - r, cx + r, cy + r], outline=color, width=4)
    f = font(SERIF_BOLD, int(r * 0.8), rng)
    w = draw.textlength(initials, font=f)
    draw.text((cx - w / 2, cy - r * 0.5), initials, font=f, fill=color)


def guilloche(draw, W, H, color, rng):
    for k in range(rng.randint(6, 14)):
        amp, freq, ph = rng.uniform(10, 40), rng.uniform(0.005, 0.02), rng.uniform(0, 6)
        y0 = rng.uniform(0, H)
        pts = [(x, y0 + amp * math.sin(freq * x + ph)) for x in range(0, W, 6)]
        draw.line(pts, fill=color, width=1)


def border(draw, W, H, color, rng):
    style = rng.randint(0, 4)
    m = rng.randint(20, 50)
    if style == 0:
        draw.rectangle([m, m, W - m, H - m], outline=color, width=8)
        draw.rectangle([m + 16, m + 16, W - m - 16, H - m - 16], outline=color, width=2)
    elif style == 1:
        for i in range(0, 14, 3):
            draw.rectangle([m + i, m + i, W - m - i, H - m - i], outline=color, width=1)
        for (x, y) in [(m, m), (W - m, m), (m, H - m), (W - m, H - m)]:
            draw.ellipse([x - 22, y - 22, x + 22, y + 22], outline=color, width=4)
    elif style == 2:
        draw.rectangle([0, 0, W, m * 2], fill=color)
        draw.rectangle([0, H - m, W, H], fill=color)
    elif style == 3:
        draw.rectangle([0, 0, m * 3, H], fill=color)
    # style 4: no border


def qr_block(draw, x, y, s, rng):
    n = 21
    c = s / n
    for i in range(n):
        for j in range(n):
            if rng.random() < 0.5 or (i < 7 and j < 7) or (i < 7 and j > 13) or (i > 13 and j < 7):
                if (i < 7 and j < 7) or (i < 7 and j > 13) or (i > 13 and j < 7):
                    edge = i in (0, 6, 14, 20) or j in (0, 6, 14, 20) or (2 <= i % 14 <= 4 and 2 <= j % 14 <= 4)
                    if not edge:
                        continue
                draw.rectangle([x + j * c, y + i * c, x + (j + 1) * c, y + (i + 1) * c], fill=(0, 0, 0))


# ----------------------------------------------------------------------------- CERTIFICATE
def gen_certificate(rng: random.Random) -> Tuple[Image.Image, str]:
    landscape = rng.random() < 0.72
    W, H = (1400, 990) if landscape else (990, 1400)
    bg, accent, ink = rng.choice(PALETTES)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    if rng.random() < 0.5:
        lite = tuple(int(b * 0.85 + a * 0.15) for b, a in zip(bg, accent))
        guilloche(d, W, H, lite, rng)
    border(d, W, H, accent, rng)

    title, kind = rng.choice(CERT_TITLES)
    person = name(rng)
    online = kind in ("completion", "participation", "internship") and rng.random() < 0.5
    issuer = rng.choice(ORGS) if online or kind == "internship" else rng.choice(INSTITUTIONS)
    initials = "".join(w[0] for w in issuer.split() if w[0].isupper())[:3]
    left = rng.random() < 0.3  # modern left-aligned layout
    cx = W // 2
    x0 = int(W * 0.12)
    y = int(H * 0.08)
    parts = [issuer, title]

    if left:
        logo(d, x0 + 40, y + 40, 40, initials, rng, accent)
        d.text((x0 + 100, y + 20), issuer, font=font(SANS_BOLD, 34, rng), fill=ink)
        y += 150
        d.text((x0, y), title, font=font(SERIF_BOLD, 58, rng), fill=accent)
        y += 100
    else:
        logo(d, cx, y + 45, 45, initials, rng, accent)
        y += 110
        y += text_center(d, cx, y, issuer, font(SERIF_BOLD, rng.randint(34, 46), rng), ink) + 12
        if rng.random() < 0.5:
            sub = rng.choice(["(Deemed to be University under section 3 of UGC Act, 1956)", "Accredited by NAAC with A++ Grade",
                              "An Autonomous Institution", "Approved by AICTE, New Delhi"])
            y += text_center(d, cx, y, sub, font(SANS, 20, rng), ink) + 10
            parts.append(sub)
        y += 30
        y += text_center(d, cx, y, title, font(SERIF_BOLD, rng.randint(52, 72), rng), accent) + 40

    intro = rng.choice(["This is to certify that", "This certificate is proudly presented to", "is awarded to",
                        "This is to certify that Mr./Ms.", "We hereby certify that"])
    fi = font(SERIF, 28, rng)
    fn = font(SCRIPT + SERIF_BOLD, rng.randint(56, 76), rng)
    if left:
        d.text((x0, y), intro, font=fi, fill=ink); y += 50
        d.text((x0, y), person, font=fn, fill=ink); y += fn.size + 30
    else:
        y += text_center(d, cx, y, intro, fi, ink) + 18
        y += text_center(d, cx, y, person, fn, ink) + 24
        d.line([cx - 260, y, cx + 260, y], fill=accent, width=2); y += 20
    parts += [intro, person]

    if kind == "degree":
        deg = rng.choice(DEGREES)
        cg = f"{rng.uniform(6.5, 9.8):.2f}"
        body = [f"has been admitted to the degree of", deg,
                rng.choice([f"with First Class with Distinction (CGPA {cg})", f"in {rng.choice(MONTHS)} {rng.randint(2016, 2026)}",
                            "having fulfilled all the requirements prescribed for the degree", f"CGPA: {cg}"])]
    elif kind == "internship":
        body = [f"has successfully completed an internship as {rng.choice(['Software Engineer Intern', 'Data Analyst Intern', 'ML Research Intern', 'Web Developer Intern'])}",
                f"at {issuer} from {date_str(rng)} to {date_str(rng)}.",
                "During the internship the performance was found to be excellent."]
    elif kind == "participation":
        body = [f"has participated in the {rng.choice(['National Level Hackathon', 'Technical Symposium', 'Workshop on Generative AI', 'International Conference on Computing', 'Coding Contest'])}",
                f"organised by {issuer} on {date_str(rng)}."]
    elif kind == "achievement":
        body = [f"for securing {rng.choice(['First', 'Second', 'Third'])} Place in {rng.choice(COURSES)}",
                f"held on {date_str(rng)}."]
    else:
        body = [f"has successfully completed the course", rng.choice(COURSES),
                rng.choice([f"with a score of {rng.randint(60, 99)}%", f"a {rng.choice([4, 8, 12])} week online course",
                            f"on {date_str(rng)}", f"with grade {rng.choice(['A', 'A+', 'O', 'B+', 'Elite', 'Gold'])}"])]
    fb = font(SERIF + SANS, rng.randint(24, 30), rng)
    for line in body:
        for ln in wrap(d, line, fb, W * 0.72):
            if left:
                d.text((x0, y), ln, font=fb, fill=ink)
                y += fb.size + 10
            else:
                y += text_center(d, cx, y, ln, fb, ink) + 10
        parts.append(line)

    # footer: signatures, date, certificate number, seal, QR
    fy = int(H * 0.8)
    fs = font(SANS, 20, rng)
    roles = rng.sample(["Registrar", "Vice Chancellor", "Controller of Examinations", "Director", "Dean Academics",
                        "Program Coordinator", "HR Manager", "Head of Department", "Chief Executive Officer"], rng.randint(1, 3))
    slots = [W * 0.2, W * 0.8, W * 0.5][:len(roles)]
    for sx, role in zip(slots, roles):
        signature(d, sx - 90, fy - 60, 180, 50, rng)
        d.line([sx - 110, fy, sx + 110, fy], fill=ink, width=1)
        text_center(d, sx, fy + 8, role, fs, ink)
        parts.append(role)
    cno = f"{initials}-{rng.randint(2016, 2026)}-{rng.randint(10000, 99999)}"
    meta = rng.choice([f"Certificate No: {cno}", f"Certificate ID: {cno}", f"Serial No. {cno}", f"Credential ID {cno}"])
    d.text((int(W * 0.08), H - int(H * 0.07)), meta, font=fs, fill=ink)
    dt = f"Date: {date_str(rng)}"
    d.text((W - int(W * 0.08) - d.textlength(dt, font=fs), H - int(H * 0.07)), dt, font=fs, fill=ink)
    parts += [meta, dt]
    if rng.random() < 0.35:
        qr_block(d, W - int(W * 0.08) - 90, int(H * 0.08), 90, rng)
    if rng.random() < 0.7:
        img = seal(img, int(W * rng.choice([0.35, 0.65, 0.5])), fy - 40, rng.randint(55, 80), rng,
                   color=rng.choice([(170, 25, 35), (20, 50, 140), (150, 110, 20)]))
    return img, "\n".join(parts)


# ----------------------------------------------------------------------------- ACADEMIC_RECORD
def letterhead(img, d, W, rng, accent, ink):
    inst = rng.choice(INSTITUTIONS)
    initials = "".join(w[0] for w in inst.split() if w[0].isupper())[:3]
    logo(d, 90, 80, 45, initials, rng, accent)
    d.text((160, 45), inst, font=font(SERIF_BOLD, rng.randint(30, 38), rng), fill=accent)
    addr = rng.choice(["Vellore, Tamil Nadu 632014", "Chennai 600127, India", "Bengaluru, Karnataka 560001",
                       "Hyderabad, Telangana 500032", "Pune, Maharashtra 411001", "Kochi, Kerala 682022"])
    d.text((160, 92), addr, font=font(SANS, 18, rng), fill=ink)
    d.line([40, 140, W - 40, 140], fill=accent, width=3)
    return inst, addr


def gen_grade_sheet(rng: random.Random) -> Tuple[Image.Image, str]:
    W, H = 1000, 1414
    bg = rng.choice([(255, 255, 255), (252, 252, 246), (246, 250, 255), (255, 250, 240)])
    _, accent, ink = rng.choice(PALETTES)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    if rng.random() < 0.4:
        guilloche(d, W, H, tuple(int(b * 0.9 + a * 0.1) for b, a in zip(bg, accent)), rng)
    inst, addr = letterhead(img, d, W, rng, accent, ink)
    title = rng.choice(["GRADE SHEET", "STATEMENT OF MARKS", "CONSOLIDATED GRADE SHEET", "ACADEMIC TRANSCRIPT",
                        "SEMESTER MARK SHEET", "PROVISIONAL GRADE CARD", "OFFICE OF THE CONTROLLER OF EXAMINATIONS - GRADE CARD"])
    ft = font(SERIF_BOLD + SANS_BOLD, 30, rng)
    text_center(d, W // 2, 165, title, ft, ink)
    parts = [inst, addr, title]

    person, reg = name(rng), reg_no(rng)
    deg = rng.choice(DEGREES)
    sem = rng.randint(1, 8)
    fields = [("Name of the Student", person), ("Register Number", reg), ("Programme", deg),
              ("Semester", str(sem) if rng.random() < 0.5 else (lambda yy: f"{rng.choice(['Fall', 'Winter'])} Semester {yy}-{(yy + 1) % 100:02d}")(rng.randint(2019, 2026))),
              ("Month & Year of Examination", f"{rng.choice(MONTHS)} {rng.randint(2018, 2026)}")]
    if rng.random() < 0.5:
        fields.append(("Date of Birth", date_str(rng, rng.randint(1998, 2007))))
    fl, fv = font(SANS_BOLD, 19, rng), font(SANS, 19, rng)
    y = 225
    for i, (k, v) in enumerate(fields):
        col = i % 2 if len(v) < 28 else 0
        x = 50 if col == 0 else 520
        d.text((x, y), f"{k}:", font=fl, fill=ink)
        d.text((x + d.textlength(f"{k}: ", font=fl), y), v, font=fv, fill=ink)
        parts.append(f"{k}: {v}")
        if col == 1 or len(v) >= 28 or i == len(fields) - 1:
            y += 34
    y += 20

    marks_mode = rng.random() < 0.3
    if marks_mode:
        cols = ["S.No", "Subject", "Max Marks", "Marks Obtained", "Result"]
        widths = [70, 440, 140, 180, 70]
    else:
        cols = ["S.No", "Course Code", "Course Title", "Credits", "Grade", "Grade Point"]
        widths = [60, 150, 430, 90, 80, 90]
    scale = (W - 100) / sum(widths)
    widths = [w * scale for w in widths]
    rows = rng.sample(SUBJECTS, rng.randint(5, 12))
    rh = 34
    fh, fr = font(SANS_BOLD, 17, rng), font(SANS + MONO, 17, rng)
    x = 50
    d.rectangle([50, y, W - 50, y + rh], fill=tuple(int(a * 0.15 + 255 * 0.85) for a in accent))
    for c, w in zip(cols, widths):
        d.text((x + 6, y + 8), c, font=fh, fill=ink)
        x += w
    parts.append(" ".join(cols))
    total_cr, total_gp = 0, 0.0
    for r, (subj, cr) in enumerate(rows):
        y += rh
        if marks_mode:
            mk = rng.randint(35, 99)
            vals = [str(r + 1), subj, "100", str(mk), "PASS" if mk >= 40 else "FAIL"]
        else:
            g, gp = rng.choice(GRADES)
            code = f"{rng.choice(['BCSE', 'CSE', 'MAT', 'PHY', 'HUM', 'EEE', 'CS'])}{rng.randint(100, 499)}{rng.choice(['L', 'P', 'T', ''])}"
            vals = [str(r + 1), code, subj, str(cr), g, str(gp)]
            total_cr += cr
            total_gp += cr * gp
        x = 50
        for v, w in zip(vals, widths):
            d.text((x + 6, y + 8), v, font=fr, fill=ink)
            x += w
        parts.append(" ".join(vals))
    y += rh
    # grid
    top = y - rh * (len(rows) + 1)
    for k in range(len(rows) + 2):
        d.line([50, top + k * rh, W - 50, top + k * rh], fill=ink, width=1)
    x = 50
    for w in widths + [0]:
        d.line([x, top, x, y], fill=ink, width=1)
        x += w
    y += 30
    fs = font(SANS_BOLD, 21, rng)
    if marks_mode:
        summ = f"Total: {rng.randint(300, 900)}    Percentage: {rng.uniform(55, 97):.2f}%    Result: PASS"
    else:
        gpa = total_gp / max(1, total_cr)
        cgpa = min(10, max(5, gpa + rng.uniform(-0.6, 0.6)))
        summ = rng.choice([f"Credits Registered: {total_cr}   Credits Earned: {total_cr}   GPA: {gpa:.2f}   CGPA: {cgpa:.2f}",
                           f"SGPA: {gpa:.2f}    CGPA: {cgpa:.2f}", f"Cumulative Grade Point Average (CGPA): {cgpa:.2f}"])
    d.text((50, y), summ, font=fs, fill=ink)
    parts.append(summ)
    y += 50
    if rng.random() < 0.5:
        leg = "Grading: S=10, A=9, B=8, C=7, D=6, E=5, F=0 (Fail), N=Absent"
        d.text((50, y), leg, font=font(SANS, 15, rng), fill=ink)
        parts.append(leg)
    fy = H - 170
    signature(d, W - 330, fy - 55, 200, 50, rng)
    role = rng.choice(["Controller of Examinations", "Registrar", "Dean - Academics", "Principal"])
    d.text((W - 340, fy + 5), role, font=font(SANS, 19, rng), fill=ink)
    dt = f"Date of Issue: {date_str(rng)}"
    d.text((50, fy + 5), dt, font=font(SANS, 19, rng), fill=ink)
    parts += [role, dt]
    if rng.random() < 0.6:
        img = seal(img, W // 2, fy - 20, 70, rng, color=rng.choice([(170, 25, 35), (20, 50, 140)]))
    if rng.random() < 0.3:
        qr_block(ImageDraw.Draw(img), W - 150, 30, 100, rng)
    return img, "\n".join(parts)


def _letter_page(rng, header_title, body_paras, sign_role):
    W, H = 1000, 1414
    _, accent, ink = rng.choice(PALETTES)
    img = Image.new("RGB", (W, H), (255, 255, 255) if rng.random() < 0.7 else (252, 250, 244))
    d = ImageDraw.Draw(img)
    inst, addr = letterhead(img, d, W, rng, accent, ink)
    parts = [inst, addr]
    fb = font(SERIF + SANS, rng.randint(20, 24), rng)
    y = 175
    ref = f"Ref: {rng.choice(['ACAD', 'COE', 'REG', 'DEAN'])}/{rng.randint(2019, 2026)}/{rng.randint(100, 9999)}"
    dt = f"Date: {date_str(rng)}"
    d.text((60, y), ref, font=fb, fill=ink)
    d.text((W - 60 - d.textlength(dt, font=fb), y), dt, font=fb, fill=ink)
    parts += [ref, dt]
    y += 70
    if header_title:
        text_center(d, W // 2, y, header_title, font(SERIF_BOLD + SANS_BOLD, 30, rng), ink)
        parts.append(header_title)
        y += 70
    for para in body_paras:
        for ln in wrap(d, para, fb, W - 140):
            d.text((70, y), ln, font=fb, fill=ink)
            y += fb.size + 12
        y += 18
        parts.append(para)
    y = max(y + 40, H - 300)
    signature(d, 70, y, 200, 50, rng)
    d.text((70, y + 60), sign_role, font=font(SANS_BOLD, 20, rng), fill=ink)
    parts.append(sign_role)
    if rng.random() < 0.5:
        img = seal(img, 420, y + 30, 65, rng)
    return img, "\n".join(parts)


def gen_completion_letter(rng: random.Random) -> Tuple[Image.Image, str]:
    person, reg, deg = name(rng), reg_no(rng), rng.choice(DEGREES)
    cg = f"{rng.uniform(6.0, 9.9):.2f}"
    kind = rng.randint(0, 2)
    if kind == 0:
        title = rng.choice(["DEGREE COMPLETION CERTIFICATE", "COURSE COMPLETION LETTER", "TO WHOM IT MAY CONCERN"])
        paras = [f"This is to certify that {person} (Register No. {reg}) was a bonafide student of this institution "
                 f"and has successfully completed all the requirements for the award of the degree of {deg}.",
                 f"The candidate has secured a Cumulative Grade Point Average (CGPA) of {cg} on a 10 point scale "
                 f"and passed in {rng.choice(['First Class with Distinction', 'First Class', 'Second Class'])}.",
                 f"The degree will be formally conferred at the next convocation. This letter is issued on request for "
                 f"{rng.choice(['higher studies', 'employment', 'visa', 'verification'])} purposes."]
    elif kind == 1:
        title = rng.choice(["BONAFIDE CERTIFICATE", "STUDENT STATUS LETTER"])
        paras = [f"This is to certify that {person}, Register Number {reg}, is a bonafide student of {deg} "
                 f"programme, currently studying in {rng.choice(['second', 'third', 'final'])} year during the academic year "
                 + (lambda yy: f"{yy}-{(yy + 1) % 100:02d}.")(rng.randint(2019, 2026)),
                 f"The student's CGPA as of the latest semester is {cg}. The student bears good conduct and character."]
    else:
        title = rng.choice(["MEDIUM OF INSTRUCTION CERTIFICATE", "RANK CERTIFICATE"])
        paras = [f"This is to certify that {person} (Reg. No. {reg}) has completed the {deg} programme, "
                 f"and the medium of instruction throughout the programme was English.",
                 f"The candidate secured a CGPA of {cg} and stood in the top {rng.randint(1, 20)}% of the class."]
    return _letter_page(rng, title, paras, rng.choice(["Registrar", "Controller of Examinations", "Dean Academics", "Principal"]))


def render_lor(text: str, rng: random.Random) -> Tuple[Image.Image, str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    body = []
    for l in lines:
        if l.isupper() and len(body) < 2:
            continue  # letterhead lines are redrawn by _letter_page
        body.append(l)
    title = rng.choice(["LETTER OF RECOMMENDATION", "", "RECOMMENDATION LETTER"])
    img, t = _letter_page(rng, title, body[:-1] if len(body) > 1 else body, body[-1] if body else "Professor")
    return img, t


# ----------------------------------------------------------------------------- OTHER_DOCUMENT
def gen_other_document(rng: random.Random) -> Tuple[Image.Image, str]:
    kind = rng.randint(0, 5)
    W, H = (1000, 1414) if kind != 1 else (600, 1100)
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    _, accent, ink = rng.choice(PALETTES)
    parts = []
    company = (_FAKE.company() if _FAKE else "Sri Lakshmi Traders") if rng.random() < 0.8 else "Sri Lakshmi Provision Store"
    if kind in (0, 1):  # invoice / receipt
        title = rng.choice(["TAX INVOICE", "INVOICE", "BILL OF SUPPLY", "RECEIPT", "CASH MEMO"])
        fb = font(MONO + SANS, 20 if kind == 0 else 22, rng)
        d.text((40, 40), company, font=font(SANS_BOLD, 34, rng), fill=accent)
        d.text((40, 90), title, font=font(SANS_BOLD, 28, rng), fill=ink)
        d.text((40, 130), f"GSTIN: 33{rng.randint(10 ** 9, 10 ** 10 - 1)}Z{rng.randint(1, 9)}   Date: {date_str(rng)}", font=fb, fill=ink)
        parts += [company, title]
        y = 190
        items = ["Rice 5kg", "Sugar 1kg", "Wheat Flour", "Toor Dal", "Sunflower Oil 1L", "Milk", "Laptop Charger",
                 "USB Cable", "Notebook", "Printer Paper A4", "Cement Bag", "Paint 4L", "Tea Powder", "Soap", "Shampoo"]
        total = 0
        d.text((40, y), "Item                 Qty    Rate    Amount", font=fb, fill=ink)
        y += 36
        for it in rng.sample(items, rng.randint(4, 12)):
            q, rate = rng.randint(1, 5), rng.randint(20, 900)
            total += q * rate
            ln = f"{it:<20} {q:>3} {rate:>7} {q * rate:>9}"
            d.text((40, y), ln, font=fb, fill=ink)
            parts.append(ln)
            y += 32
        tax = total * 0.18
        for ln in [f"Sub Total: {total:.2f}", f"GST 18%: {tax:.2f}", f"Grand Total: Rs. {total + tax:.2f}", "Thank you! Visit again"]:
            y += 34
            d.text((40, y), ln, font=font(SANS_BOLD, 22, rng), fill=ink)
            parts.append(ln)
    elif kind == 2:  # article / newsletter
        head = sentence(rng, 7).rstrip(".")
        d.text((50, 50), rng.choice(["The Daily Chronicle", "Tech Weekly", "Campus Newsletter", "Market Watch"]),
               font=font(SERIF_BOLD, 44, rng), fill=ink)
        d.line([50, 110, W - 50, 110], fill=ink, width=3)
        fh = font(SERIF_BOLD, 34, rng)
        y = 130
        for ln in wrap(d, head, fh, W - 100):
            d.text((50, y), ln, font=fh, fill=ink); y += 44
        parts.append(head)
        fb = font(SERIF, 19, rng)
        colw = (W - 130) // 2
        for c in range(2):
            yy = y + 20
            while yy < H - 80:
                p = paragraph(rng, 3)
                for ln in wrap(d, p, fb, colw):
                    if yy > H - 80:
                        break
                    d.text((50 + c * (colw + 30), yy), ln, font=fb, fill=ink); yy += 26
                    parts.append(ln)
                yy += 14
    elif kind == 3:  # menu
        d.rectangle([0, 0, W, H], fill=rng.choice([(40, 30, 25), (250, 240, 220), (20, 40, 35)]))
        light = img.getpixel((5, 5))[0] < 128
        col = (240, 230, 210) if light else (60, 30, 20)
        text_center(d, W // 2, 60, rng.choice(["MENU", "Today's Specials", "Cafe Menu", "Restaurant Menu"]), font(SCRIPT + SERIF_BOLD, 70, rng), col)
        y = 200
        dishes = ["Masala Dosa", "Idli Vada", "Paneer Butter Masala", "Veg Biryani", "Chicken 65", "Filter Coffee",
                  "Cappuccino", "Margherita Pizza", "Pasta Alfredo", "Chocolate Brownie", "Fresh Lime Soda", "Parotta"]
        for ds in rng.sample(dishes, rng.randint(7, 12)):
            ln = f"{ds}"
            pr = f"Rs {rng.randint(40, 450)}"
            d.text((100, y), ln, font=font(SERIF, 30, rng), fill=col)
            d.text((W - 220, y), pr, font=font(SERIF, 30, rng), fill=col)
            parts.append(f"{ln} {pr}")
            y += 80
    elif kind == 4:  # notice / poster / event flyer
        d.rectangle([0, 0, W, H], fill=tuple(int(a * 0.25 + 255 * 0.75) for a in accent))
        text_center(d, W // 2, 120, rng.choice(["NOTICE", "SALE!", "WORKSHOP", "HIRING NOW", "LOST AND FOUND", "PUBLIC NOTICE"]),
                    font(SANS_BOLD, 100, rng), accent)
        fb = font(SANS, 30, rng)
        y = 320
        for ln in wrap(d, paragraph(rng, 4), fb, W - 160):
            d.text((80, y), ln, font=fb, fill=ink); y += 44; parts.append(ln)
    else:  # bank statement / spreadsheet like
        d.text((40, 40), company, font=font(SANS_BOLD, 30, rng), fill=accent)
        d.text((40, 85), rng.choice(["Account Statement", "Quarterly Budget Report", "Inventory List", "Timesheet"]),
               font=font(SANS_BOLD, 24, rng), fill=ink)
        fb = font(MONO, 17, rng)
        y = 140
        for r in range(rng.randint(15, 30)):
            ln = f"{date_str(rng)}  {sentence(rng, 3)[:28]:<28} {rng.randint(100, 99999):>9}.00  {rng.randint(1000, 999999):>10}.00"
            d.text((40, y), ln, font=fb, fill=ink); y += 30; parts.append(ln)
            d.line([40, y - 4, W - 40, y - 4], fill=(210, 210, 210), width=1)
    return img, "\n".join(parts)


# ----------------------------------------------------------------------------- augmentations
def _desk_background(size, rng, photos: Optional[List[Image.Image]] = None):
    W, H = size
    if photos and rng.random() < 0.45:
        p = rng.choice(photos).convert("RGB").resize((W, H))
        return p.filter(ImageFilter.GaussianBlur(rng.uniform(2, 8)))
    base = np.array(rng.choice([(120, 85, 55), (160, 120, 80), (60, 60, 65), (200, 200, 195), (90, 60, 40),
                                (30, 30, 35), (180, 170, 150), (70, 90, 110)]), dtype=np.float32)
    noise = np.random.default_rng(rng.randint(0, 10 ** 6)).normal(0, rng.uniform(4, 18), (H, W, 1))
    grain = np.sin(np.linspace(0, rng.uniform(20, 80), W))[None, :, None] * rng.uniform(0, 12)
    arr = np.clip(base[None, None, :] + noise + grain, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def phone_photo(doc: Image.Image, rng: random.Random, photos: Optional[List[Image.Image]] = None) -> Image.Image:
    """Simulate a phone camera shot of a printed document lying on a surface."""
    dw, dh = doc.size
    portrait = dh >= dw
    W, H = (900, 1200) if portrait else (1200, 900)
    bg = _desk_background((W, H), rng, photos)
    fill = rng.uniform(0.62, 0.92)
    s = min(W * fill / dw, H * fill / dh)
    tw, th = dw * s, dh * s
    cx, cy = W / 2 + rng.uniform(-0.06, 0.06) * W, H / 2 + rng.uniform(-0.06, 0.06) * H
    j = lambda: rng.uniform(-0.06, 0.06) * min(W, H)
    dst = np.float32([[cx - tw / 2 + j(), cy - th / 2 + j()], [cx + tw / 2 + j(), cy - th / 2 + j()],
                      [cx + tw / 2 + j(), cy + th / 2 + j()], [cx - tw / 2 + j(), cy + th / 2 + j()]])
    src = np.float32([[0, 0], [dw, 0], [dw, dh], [0, dh]])
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(np.array(doc), M, (W, H))
    mask = cv2.warpPerspective(np.full((dh, dw), 255, np.uint8), M, (W, H))
    out = np.array(bg).copy()
    out[mask > 0] = warped[mask > 0]
    out = out.astype(np.float32)
    # lighting gradient + shadow
    gx = np.linspace(rng.uniform(0.7, 1.0), rng.uniform(0.85, 1.15), W)[None, :]
    gy = np.linspace(rng.uniform(0.8, 1.05), rng.uniform(0.85, 1.1), H)[:, None]
    out *= (gx * gy)[..., None]
    if rng.random() < 0.4:
        x0 = rng.randint(0, W)
        out[:, x0:x0 + rng.randint(80, 300)] *= rng.uniform(0.6, 0.85)
    tint = np.array([rng.uniform(0.92, 1.05), rng.uniform(0.95, 1.03), rng.uniform(0.88, 1.02)])
    out = np.clip(out * tint, 0, 255).astype(np.uint8)
    img = Image.fromarray(out)
    if rng.random() < 0.6:
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 1.4)))
    return img


def scan_effect(doc: Image.Image, rng: random.Random) -> Image.Image:
    """Photocopy / flatbed scan look: grayscale, slight skew, speckle noise."""
    img = doc
    if rng.random() < 0.7:
        img = img.convert("L").convert("RGB")
    img = img.rotate(rng.uniform(-2.5, 2.5), expand=False, fillcolor=(255, 255, 255))
    arr = np.array(img).astype(np.int16)
    noise = np.random.default_rng(rng.randint(0, 10 ** 6)).normal(0, rng.uniform(2, 10), arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    if rng.random() < 0.5:
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 0.9)))
    return img


def tint_scan(doc: Image.Image, rng: random.Random) -> Image.Image:
    """Give grayscale scans a paper colour so colour alone never gives the class away."""
    arr = np.array(doc.convert("L")).astype(np.float32) / 255.0
    paper = np.array(rng.choice(PALETTES)[0], dtype=np.float32)
    ink = np.array(rng.choice([(20, 20, 30), (30, 30, 80), (40, 20, 20)]), dtype=np.float32)
    out = ink[None, None, :] + (paper - ink)[None, None, :] * arr[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
