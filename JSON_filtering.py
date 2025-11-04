import pandas as pd
import ast, json, re
from pathlib import Path
from datetime import datetime

# 설정
CODEBOOK_PATH = "codebook.csv"
DATA_PATH = "data.csv"
OUT_JSONL = "records.jsonl"
CURRENT_YEAR = 2025
ID_COLUMNS = ["mb_sn", "id"]

# --- helpers
def safe_read_csv_utf8sig(path):
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False).fillna("")

def parse_options_raw(opts_raw):
    if not opts_raw or str(opts_raw).strip() == "":
        return {}
    s = str(opts_raw).strip()
    try:
        return ast.literal_eval(s)
    except Exception:
        try:
            return json.loads(s.replace("'", '"'))
        except Exception:
            return {}

def normalize_key_for_mapping(v):
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            if float(v).is_integer():
                return str(int(v))
            return str(v).strip()
    except Exception:
        pass
    s = str(v).strip()
    if s == "":
        return None
    m = re.fullmatch(r'(-?\d+)\.0+$', s)
    if m:
        return m.group(1)
    m2 = re.fullmatch(r'-?\d+\.\d+', s)
    if m2:
        try:
            f = float(s)
            if f.is_integer():
                return str(int(f))
        except:
            pass
    return s

def strip_parentheses_content(label):
    """
    라벨에서 괄호와 괄호 내부 내용을 제거하고 앞뒤 공백 정리.
    예: "삼성전자 (갤럭시, 노트)" -> "삼성전자"
    """
    if label is None:
        return None
    s = str(label)
    # remove (...) and full-width parentheses too
    s = re.sub(r'（.*?）|\(.*?\)', '', s)
    s = s.strip()
    return s if s != "" else None

def load_codebook(path):
    cb = safe_read_csv_utf8sig(path)
    meta = {}
    for _, r in cb.iterrows():
        var = str(r.get('variable','')).strip()
        if not var:
            continue
        qtype = (r.get('type','') or "").strip().upper()
        raw_opts = parse_options_raw(r.get('options_json','') or "")
        # norm_options: normalized key -> cleaned label (parentheses stripped)
        norm_opts = {}
        if isinstance(raw_opts, dict):
            for ok, ov in raw_opts.items():
                nk = normalize_key_for_mapping(ok)
                if nk is None:
                    continue
                norm_opts[nk] = ov
        meta[var] = {
            "type": qtype,
            "options": raw_opts if isinstance(raw_opts, dict) else {},
            "norm_options": norm_opts,
            "question_text": r.get('question_text','') or ""
        }
    return meta

def to_int_or_none(x):
    try:
        if x is None: return None
        s = str(x).strip()
        if s == "": return None
        # remove non-digit except leading minus
        num = re.sub(r'[^\d\-]', '', s)
        if num == "" or num == "-" : return None
        return int(float(num))
    except:
        return None

def parse_multi(value):
    if value is None: return []
    s = str(value).strip()
    if s == "": return []
    parts = re.split(r'[,\|;]+', s)
    return [p.strip() for p in parts if p.strip() != ""]

def map_single(value, meta_opts):
    """
    meta_opts: dict with keys 'options' and 'norm_options'
    반환: cleaned label (괄호 제거) or None
    """
    if value is None:
        return None
    key = normalize_key_for_mapping(value)
    if key is None:
        return None
    norm_opts = meta_opts.get('norm_options') if isinstance(meta_opts, dict) else {}
    raw_opts = meta_opts.get('options') if isinstance(meta_opts, dict) else {}
    # norm_options 우선
    if norm_opts and key in norm_opts:
        return norm_opts[key]
    if raw_opts and key in raw_opts:
        return raw_opts[key]
    if raw_opts:
        for ok, ov in raw_opts.items():
            if normalize_key_for_mapping(ok) == key:
                return ov
    # no mapping -> clean the original string value (strip parentheses too)
    return value

def map_multi_codes(codes, meta_opts):
    if codes is None:
        return []
    if isinstance(codes, (list, tuple)):
        parts = codes
    else:
        parts = parse_multi(codes)
    out = []
    for p in parts:
        lbl = map_single(p, meta_opts)
        if lbl is not None:
            out.append(lbl)
    return out

def parse_q2_birth(q2_raw):
    if q2_raw is None:
        return None, None
    s = str(q2_raw).strip()
    if s == "":
        return None, None
    m = re.search(r'(\d{2,4})\s*년\s*([0-1]?\d|00)\s*월', s)
    if not m:
        m2 = re.search(r'(\d{4})[^\d]+([0-1]?\d|00)[^\d]+(\d{1,2}|00)', s)
        if not m2:
            return None, None
        year_str, month_str = m2.group(1), m2.group(2)
    else:
        year_str, month_str = m.group(1), m.group(2)
    try:
        if len(year_str) == 2:
            return None, None
        birth_year = int(year_str)
    except:
        birth_year = None
    try:
        month_int = int(month_str)
        birth_month = month_int if month_int != 0 else None
    except:
        birth_month = None
    return birth_year, birth_month

def age_group_from_birth_year(birth_year, current_year=CURRENT_YEAR):
    if birth_year is None:
        return None
    try:
        age = current_year - int(birth_year) + 1
    except:
        return None
    if age < 20:
        return "10s"
    if age < 30:
        return "20s"
    if age < 40:
        return "30s"
    if age < 50:
        return "40s"
    if age < 60:
        return "50s"
    return "60+"

def normalize_region(level1, level2):
    def norm(s):
        if not s: return None
        t = str(s).strip()
        t = t.replace("특별시","").replace("광역시","").replace("시 ","").replace("시","").replace("도","").strip()
        return t or None
    return norm(level1), norm(level2)

def pick_id_from_row(raw):
    for c in ID_COLUMNS:
        v = raw.get(c)
        if v not in (None, "", "nan"):
            return str(v)
    return None

def normalize_raw_row(row):
    norm = {}
    for k, v in row.items():
        if isinstance(v, str):
            s = v.strip()
            norm[k] = s if s != "" else None
        else:
            norm[k] = v if v is not None else None
    return norm

# --- profile builder (Q0..Q13)
def build_profile_from_response(response):
    profile = {}
    # Q0 carrier
    profile['carrier'] = response.get('Q0')

    # Q1 sex
    profile['sex'] = response.get('Q1')

    # Q2 birth
    q2_raw = response.get('Q2')
    by, bm = parse_q2_birth(q2_raw)
    profile['birth_year'] = by
    profile['birth_month'] = bm
    profile['age_group'] = age_group_from_birth_year(by)

    # Q3 region
    lvl1 = response.get('Q3_1')
    lvl2 = response.get('Q3_2')
    r1, r2 = normalize_region(lvl1, lvl2)
    profile['region'] = {"level1": r1, "level2": r2}

    # Q4 marital_status
    profile['marital_status'] = strip_parentheses_content(response.get('Q4'))

    # Q5 children_count
    profile['children_count'] = response.get('Q5')

    # Q6 family_size
    profile['family_size'] = to_int_or_none(response.get('Q6'))
    '''
    if 'Q6' in codebook_meta:
        mapped = map_single(response.get('Q6'), codebook_meta['Q6'])
        if mapped is not None:
            # mapped label may be like "3명" or "3"; extract integer
            profile['family_size'] = to_int_or_none(mapped)
        else:
            profile['family_size'] = to_int_or_none(response.get('Q6'))
    else:
        profile['family_size'] = to_int_or_none(raw_norm.get('Q6'))
    '''

    # Q7 education
    profile['education'] = strip_parentheses_content(response.get('Q7'))

    # Q8 occupation / job_role
    profile['occupation'] = strip_parentheses_content(response.get('Q8'))
    profile['job_role'] = strip_parentheses_content(response.get('Q8_1'))

    # Q9 / Q10 income
    profile['income_person'] = strip_parentheses_content(response.get('Q9'))
    profile['income_household'] = strip_parentheses_content(response.get('Q10'))

    # Q11 ownership products (MULTI)
    profile['ownership_products'] = strip_parentheses_content(response.get('Q11'))

    # Q12 device
    profile['device'] = {"brand": strip_parentheses_content(response.get('Q12_1')), "model": strip_parentheses_content(response.get('Q12_2'))}

    # Q13 has_car
    profile['has_car'] = None
    if isinstance(response.get('Q13'), str) and response.get('Q13') in ("있다", "있다'","있다'"):
        profile['has_car'] = True
    elif isinstance(response.get('Q13'), str) and response.get('Q13') in ("없다", "없다'"):
        profile['has_car'] = False
    else:
        if (response.get('Q14_1') and str(response.get('Q14_1')).strip() != "") or (response.get('Q14_2') and str(response.get('Q14_2')).strip() != ""):
            profile['has_car'] = True
        else:
            profile['has_car'] = None

    return profile

def build_response_from_row(raw_norm, codebook_meta):
    response = {}
    #elif re.search(r'_ETC$', var):
    for var, meta in codebook_meta.items():
        qtype = meta.get('type')
        if qtype == "STRING": # Q0, Q2, Q3_1, Q3_2
            response[var] = raw_norm.get(var) if var not in (None, "") else None
        elif qtype == "NUMERIC": # Q5
            response[var] = int(float(raw_norm.get(var))) if raw_norm.get(var) not in (None, "") else None
        elif qtype == "MULTI":
            response[var] = map_multi_codes(raw_norm.get(var), meta) if raw_norm.get(var) not in (None, "") else []
        else: # qtype == "SINGLE"
            response[var] = map_single(raw_norm.get(var), meta) if raw_norm.get(var) not in (None, "") else None
    return response


# --- main
def build_records(codebook_path, data_path, out_jsonl_path):
    codebook_meta = load_codebook(codebook_path)
    df = safe_read_csv_utf8sig(data_path)

    out_path = Path(out_jsonl_path)
    with out_path.open("w", encoding="utf-8") as f:
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            raw_norm = normalize_raw_row(row_dict)
            rid = pick_id_from_row(raw_norm) or f"row_{idx+1}"
            response = build_response_from_row(raw_norm, codebook_meta)
            profile = build_profile_from_response(response)
            rec = {"id": str(rid), "raw": raw_norm, "response": response, "profile": profile}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return len(df)

if __name__ == "__main__":
    n = build_records(CODEBOOK_PATH, DATA_PATH, OUT_JSONL)
    print(f"Wrote {n} records to {OUT_JSONL}")