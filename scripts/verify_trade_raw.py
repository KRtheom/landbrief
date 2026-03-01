import collections
import json
import os
import py_compile
import sqlite3
import sys


DB_DEFAULT = os.path.expanduser("~/real_estate_report/data/real_estate.db")
OUT_DEFAULT = os.path.join("logs", "verify_trade_raw_result.txt")
STATUS_ORDER = {"PASS": 0, "WARN": 1, "FAIL": 2}


class Tee:
    def __init__(self, path):
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        self.fp = open(path, "w", encoding="utf-8")

    def line(self, text=""):
        print(text)
        self.fp.write(text + "\n")
        self.fp.flush()

    def close(self):
        self.fp.close()


def parse_args(argv):
    db_path, out_path, sample_mod = DB_DEFAULT, OUT_DEFAULT, 1
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("--db", "--db-path"):
            db_path = os.path.expanduser(argv[i + 1])
            i += 2
        elif a in ("--output", "--out"):
            out_path = argv[i + 1]
            i += 2
        elif a == "--sample-mod":
            sample_mod = int(argv[i + 1])
            if sample_mod < 1:
                raise ValueError("--sample-mod must be >= 1")
            i += 2
        else:
            raise ValueError("unknown arg: {0}".format(a))
    return db_path, out_path, sample_mod


def register_udf(conn):
    def t(v):
        return "" if v is None else str(v)

    def has_repl(v):
        return 1 if "\ufffd" in t(v) else 0

    def has_ctrl(v):
        for ch in t(v):
            if ord(ch) < 32:
                return 1
        return 0

    def has_euckr_hint(v):
        c = 0
        for ch in t(v):
            o = ord(ch)
            if 176 <= o <= 254:
                c += 1
        return 1 if c >= 2 else 0

    def has_lower(v):
        s = t(v)
        for ch in s:
            if "a" <= ch <= "z":
                return 1
        return 0

    def has_ws(v):
        s = t(v)
        for ch in s:
            if ch in (" ", "\t", "\n", "\r"):
                return 1
        return 0

    def has_non_digit(v):
        s = t(v)
        if not s:
            return 0
        for ch in s:
            if ch.isdigit() or ch in (",", " ", "\t", "\n", "\r"):
                continue
            return 1
        return 0

    def only_digits(v):
        s = t(v).strip()
        if not s:
            return 0
        return 1 if s.isdigit() else 0

    def is_ts(v):
        s = t(v).strip()
        if len(s) < 19:
            return 0
        if not (s[4] == "-" and s[7] == "-" and s[10] in (" ", "T") and s[13] == ":" and s[16] == ":"):
            return 0
        p1 = s[0:10].replace("-", "")
        p2 = s[11:19].replace(":", "")
        return 1 if (p1.isdigit() and p2.isdigit()) else 0

    conn.create_function("has_repl", 1, has_repl)
    conn.create_function("has_ctrl", 1, has_ctrl)
    conn.create_function("has_euckr_hint", 1, has_euckr_hint)
    conn.create_function("has_lower", 1, has_lower)
    conn.create_function("has_ws", 1, has_ws)
    conn.create_function("has_non_digit", 1, has_non_digit)
    conn.create_function("only_digits", 1, only_digits)
    conn.create_function("is_ts", 1, is_ts)


def set_status(sec, new_status):
    if STATUS_ORDER[new_status] > STATUS_ORDER[sec["status"]]:
        sec["status"] = new_status


def sec(code, title):
    return {"code": code, "title": title, "status": "PASS", "details": []}


def emit(logger, section):
    logger.line("[{0}] {1}".format(section["code"], section["title"]))
    logger.line("상태: {0}".format(section["status"]))
    for d in section["details"]:
        logger.line(d)
    logger.line("")


def rows_to_lines(rows, headers):
    if not rows:
        return []
    out = [" | ".join(headers)]
    for r in rows:
        out.append(" | ".join("NULL" if v is None else str(v) for v in r))
    return out


def sample_clause(sample_mod):
    if sample_mod <= 1:
        return "", "전수(100%)"
    return " WHERE (rowid % {0}) = 0 ".format(sample_mod), "샘플(1/{0})".format(sample_mod)


def run():
    db_path, out_path, sample_mod = parse_args(sys.argv)
    logger = Tee(out_path)
    summary = collections.Counter()
    sections = []
    conn = None
    try:
        if not os.path.exists(db_path):
            raise FileNotFoundError("DB file not found: {0}".format(db_path))
        conn = sqlite3.connect("file:{0}?mode=ro".format(db_path), uri=True)
        conn.row_factory = sqlite3.Row
        register_udf(conn)

        fact_cols = [r[1] for r in conn.execute("PRAGMA table_info(fact_trade_raw)").fetchall()]
        log_cols = [r[1] for r in conn.execute("PRAGMA table_info(etl_trade_raw_log)").fetchall()]
        fset = set(fact_cols)
        total = conn.execute("SELECT COUNT(*) FROM fact_trade_raw").fetchone()[0]
        ts = conn.execute("SELECT strftime('%Y-%m-%dT%H:%M:%SZ','now')").fetchone()[0]

        logger.line("========================================")
        logger.line("fact_trade_raw 데이터 검증 결과")
        logger.line("실행 시각: {0}".format(ts))
        logger.line("DB: {0}".format(db_path))
        logger.line("총 건수: {0}".format(total))
        logger.line("========================================")
        logger.line("")

        # A-1
        s = sec("A-1", "한글 깨짐 탐지")
        cmap = collections.OrderedDict([
            ("umd", ["umd", "umd_nm"]),
            ("dong", ["dong", "apt_dong"]),
            ("apt_name", ["apt_name", "bldg_nm"]),
            ("road_nm", ["road_nm"]),
            ("dealer", ["dealer", "estate_agent"]),
            ("buyer", ["buyer", "buyer_gbn"]),
        ])
        selected = collections.OrderedDict()
        for k, arr in cmap.items():
            for c in arr:
                if c in fset:
                    selected[k] = c
                    break
        missing = [k for k in cmap if k not in selected]
        if missing:
            set_status(s, "WARN")
            s["details"].append("요청 컬럼 미존재/대체: {0}".format(", ".join(missing)))
        s["details"].append("컬럼 매핑: {0}".format(json.dumps(selected, ensure_ascii=False)))
        if not selected:
            set_status(s, "FAIL")
            s["details"].append("검증 가능한 컬럼 없음")
        else:
            exprs = []
            for k, c in selected.items():
                exprs.append("SUM(has_repl({0})) AS {1}_repl".format(c, k))
                exprs.append("SUM(has_ctrl({0})) AS {1}_ctrl".format(c, k))
                exprs.append("SUM(has_euckr_hint({0})) AS {1}_euckr".format(c, k))
                exprs.append("SUM(CASE WHEN has_repl({0})=1 OR has_ctrl({0})=1 OR has_euckr_hint({0})=1 THEN 1 ELSE 0 END) AS {1}_any".format(c, k))
            r = conn.execute("SELECT {0} FROM fact_trade_raw".format(", ".join(exprs))).fetchone()
            for k, c in selected.items():
                any_cnt = r["{0}_any".format(k)] or 0
                s["details"].append("- {0}({1}): 이상 {2}건 (U+FFFD={3}, 제어문자={4}, EUC-KR의심={5})".format(
                    k, c, any_cnt, r["{0}_repl".format(k)] or 0, r["{0}_ctrl".format(k)] or 0, r["{0}_euckr".format(k)] or 0
                ))
                if any_cnt > 0:
                    set_status(s, "WARN")
                    q = "SELECT trade_type, deal_year, deal_month, {0} FROM fact_trade_raw WHERE has_repl({0})=1 OR has_ctrl({0})=1 OR has_euckr_hint({0})=1 LIMIT 5".format(c)
                    smp = conn.execute(q).fetchall()
                    s["details"].append("  샘플:")
                    for ln in rows_to_lines(smp, ["trade_type", "deal_year", "deal_month", c]):
                        s["details"].append("  " + ln)
        sections.append(s)

        # A-2
        s = sec("A-2", "cdeal_type 대소문자 불일치")
        if "cdeal_type" not in fset:
            set_status(s, "FAIL")
            s["details"].append("cdeal_type 컬럼 없음")
        else:
            rows = conn.execute("SELECT DISTINCT trade_type, cdeal_type FROM fact_trade_raw ORDER BY trade_type, cdeal_type").fetchall()
            lower = 0
            s["details"].append("trade_type | cdeal_type | 소문자포함")
            for r in rows:
                v = "" if r["cdeal_type"] is None else str(r["cdeal_type"])
                has = any("a" <= ch <= "z" for ch in v)
                if has:
                    lower += 1
                s["details"].append("{0} | {1} | {2}".format(r["trade_type"], r["cdeal_type"], "Y" if has else "N"))
            if lower > 0:
                set_status(s, "WARN")
                s["details"].append("소문자 포함 distinct: {0}건".format(lower))
        sections.append(s)

        # A-3, A-4, D-1 combined
        trows = conn.execute(
            "SELECT trade_type, COUNT(*) AS cnt, SUM(has_lower(road_nm)) AS road_lower, "
            "SUM(CASE WHEN instr(CAST(deal_amount AS TEXT), ',')>0 THEN 1 ELSE 0 END) AS amt_comma, "
            "SUM(has_ws(deal_amount)) AS amt_ws, SUM(has_non_digit(deal_amount)) AS amt_nondigit "
            "FROM fact_trade_raw GROUP BY trade_type ORDER BY cnt DESC"
        ).fetchall()
        tcnt = {r["trade_type"]: r["cnt"] for r in trows}

        s = sec("A-3", "road_nm 대소문자 확인")
        all_lower = 0
        s["details"].append("trade_type | lowercase_count")
        for r in trows:
            c = r["road_lower"] or 0
            all_lower += c
            s["details"].append("{0} | {1}".format(r["trade_type"], c))
        s["details"].append("전체 소문자 포함 건수: {0}".format(all_lower))
        if all_lower > 0:
            set_status(s, "WARN")
            smp = conn.execute("SELECT trade_type, deal_year, deal_month, road_nm FROM fact_trade_raw WHERE has_lower(road_nm)=1 LIMIT 5").fetchall()
            for ln in rows_to_lines(smp, ["trade_type", "deal_year", "deal_month", "road_nm"]):
                s["details"].append(ln)
        sections.append(s)

        s = sec("A-4", "deal_amount 포맷 확인")
        s["details"].append("trade_type | comma | whitespace | non_digit_char")
        tc, tw, tn = 0, 0, 0
        for r in trows:
            c1, c2, c3 = (r["amt_comma"] or 0), (r["amt_ws"] or 0), (r["amt_nondigit"] or 0)
            tc, tw, tn = tc + c1, tw + c2, tn + c3
            s["details"].append("{0} | {1} | {2} | {3}".format(r["trade_type"], c1, c2, c3))
        s["details"].append("전체: comma={0}, whitespace={1}, non_digit_char={2}".format(tc, tw, tn))
        if tc > 0 or tw > 0 or tn > 0:
            set_status(s, "WARN")
            smp = conn.execute(
                "SELECT trade_type, deal_year, deal_month, deal_amount FROM fact_trade_raw "
                "WHERE instr(CAST(deal_amount AS TEXT), ',')>0 OR has_ws(deal_amount)=1 OR has_non_digit(deal_amount)=1 LIMIT 5"
            ).fetchall()
            for ln in rows_to_lines(smp, ["trade_type", "deal_year", "deal_month", "deal_amount"]):
                s["details"].append(ln)
        sections.append(s)

        # B-1
        s = sec("B-1", "컬럼별 NULL / 빈문자열 / 실데이터 건수")
        w, label = sample_clause(sample_mod)
        s["details"].append("기준: {0}".format(label))
        qparts = ["trade_type", "COUNT(*) AS total_cnt"]
        for c in fact_cols:
            qparts.append("SUM(CASE WHEN {0} IS NULL THEN 1 ELSE 0 END) AS {0}__null".format(c))
            qparts.append("SUM(CASE WHEN {0} IS NOT NULL AND CAST({0} AS TEXT)='' THEN 1 ELSE 0 END) AS {0}__blank".format(c))
            qparts.append("SUM(CASE WHEN {0} IS NOT NULL AND CAST({0} AS TEXT)!='' THEN 1 ELSE 0 END) AS {0}__value".format(c))
        q = "SELECT {0} FROM fact_trade_raw {1} GROUP BY trade_type ORDER BY trade_type".format(", ".join(qparts), w)
        b1 = conn.execute(q).fetchall()
        s["details"].append("형식: trade_type | column | null | blank | value")
        for r in b1:
            s["details"].append("- trade_type={0}".format(r["trade_type"]))
            for c in fact_cols:
                s["details"].append("  {0} | {1} | {2} | {3}".format(c, r["{0}__null".format(c)] or 0, r["{0}__blank".format(c)] or 0, r["{0}__value".format(c)] or 0))
        sections.append(s)

        # C-1
        s = sec("C-1", "dedup_key NULL 검사")
        if "dedup_key" not in fset:
            set_status(s, "FAIL")
            s["details"].append("dedup_key 컬럼 없음")
        else:
            n = conn.execute("SELECT COUNT(*) FROM fact_trade_raw WHERE dedup_key IS NULL").fetchone()[0]
            s["details"].append("dedup_key IS NULL: {0}".format(n))
            if n > 0:
                set_status(s, "WARN")
                rows = conn.execute("SELECT trade_type, COUNT(*) cnt FROM fact_trade_raw WHERE dedup_key IS NULL GROUP BY trade_type ORDER BY cnt DESC").fetchall()
                for r in rows:
                    s["details"].append("{0} | {1}".format(r["trade_type"], r["cnt"]))
                smp = conn.execute("SELECT id, trade_type, deal_year, deal_month, dedup_key FROM fact_trade_raw WHERE dedup_key IS NULL LIMIT 5").fetchall()
                for ln in rows_to_lines(smp, ["id", "trade_type", "deal_year", "deal_month", "dedup_key"]):
                    s["details"].append(ln)
        sections.append(s)

        # C-2
        s = sec("C-2", "dedup_key 중복 검사")
        if "dedup_key" not in fset:
            set_status(s, "FAIL")
            s["details"].append("dedup_key 컬럼 없음")
        else:
            w, label = sample_clause(sample_mod)
            cte = ("WITH dup AS (SELECT dedup_key, COUNT(*) cnt FROM fact_trade_raw {0} GROUP BY dedup_key HAVING COUNT(*)>1) ").format(w)
            r = conn.execute(cte + "SELECT COUNT(*) AS k, COALESCE(SUM(cnt),0) AS s FROM dup").fetchone()
            dk, ds = r["k"] or 0, r["s"] or 0
            s["details"].append("기준: {0}".format(label))
            s["details"].append("중복 dedup_key 수: {0}".format(dk))
            s["details"].append("중복 행 수 합계: {0}".format(ds))
            if dk > 0:
                set_status(s, "WARN")
                rows = conn.execute(
                    cte + "SELECT d.dedup_key, d.cnt, group_concat(DISTINCT f.trade_type) AS trade_types, "
                    "MIN(f.deal_year) AS min_y, MAX(f.deal_year) AS max_y, MIN(f.deal_month) AS min_m, MAX(f.deal_month) AS max_m "
                    "FROM dup d JOIN fact_trade_raw f ON f.dedup_key=d.dedup_key "
                    "GROUP BY d.dedup_key, d.cnt ORDER BY d.cnt DESC, d.dedup_key LIMIT 10"
                ).fetchall()
                for ln in rows_to_lines(rows, ["dedup_key", "cnt", "trade_types", "min_deal_year", "max_deal_year", "min_deal_month", "max_deal_month"]):
                    s["details"].append(ln)
        sections.append(s)

        # C-3
        s = sec("C-3", "id (PK) 연속성·중복 검사")
        r = conn.execute("SELECT MIN(id) min_id, MAX(id) max_id, COUNT(*) cnt, COUNT(DISTINCT id) dcnt FROM fact_trade_raw").fetchone()
        min_id, max_id, cnt, dcnt = r["min_id"], r["max_id"], r["cnt"], r["dcnt"]
        gap = (max_id - min_id + 1) != cnt if (min_id is not None and max_id is not None) else False
        dup = cnt - dcnt
        s["details"].append("MIN={0}, MAX={1}, COUNT={2}, DISTINCT={3}, GAP={4}, DUP={5}".format(min_id, max_id, cnt, dcnt, "Y" if gap else "N", dup))
        if gap or dup > 0:
            set_status(s, "WARN")
        sections.append(s)

        # D-1
        s = sec("D-1", "trade_type별 건수 분포")
        s["details"].append("trade_type | count")
        for r in trows:
            s["details"].append("{0} | {1}".format(r["trade_type"], r["cnt"]))
        if "LAND_SALE" in tcnt:
            s["details"].append("참고: LAND_SALE={0} (수집 미완 상태에서는 적은 건수가 정상)".format(tcnt["LAND_SALE"]))
        sections.append(s)

        # D-2
        s = sec("D-2", "날짜 범위 확인")
        rows = conn.execute(
            "SELECT trade_type, MIN(CAST(deal_year AS INTEGER)) AS min_y, MAX(CAST(deal_year AS INTEGER)) AS max_y, "
            "MIN(CAST(deal_month AS INTEGER)) AS min_m, MAX(CAST(deal_month AS INTEGER)) AS max_m, "
            "SUM(CASE WHEN only_digits(deal_year)=1 AND CAST(deal_year AS INTEGER)<2020 THEN 1 ELSE 0 END) AS pre2020, "
            "SUM(CASE WHEN deal_month IS NOT NULL AND CAST(deal_month AS TEXT)!='' AND (only_digits(deal_month)=0 OR CAST(deal_month AS INTEGER) NOT BETWEEN 1 AND 12) THEN 1 ELSE 0 END) AS bad_m, "
            "SUM(CASE WHEN deal_day IS NULL OR CAST(deal_day AS TEXT)='' THEN 1 ELSE 0 END) AS null_d, "
            "SUM(CASE WHEN deal_day IS NOT NULL AND CAST(deal_day AS TEXT)!='' AND (only_digits(deal_day)=0 OR CAST(deal_day AS INTEGER) NOT BETWEEN 1 AND 31) THEN 1 ELSE 0 END) AS bad_d "
            "FROM fact_trade_raw GROUP BY trade_type ORDER BY trade_type"
        ).fetchall()
        p, bm, bd = 0, 0, 0
        for ln in rows_to_lines(rows, ["trade_type", "min_year", "max_year", "min_month", "max_month", "pre_2020", "month_invalid", "day_null", "day_invalid"]):
            s["details"].append(ln)
        for r in rows:
            p += r["pre2020"] or 0
            bm += r["bad_m"] or 0
            bd += r["bad_d"] or 0
        if p > 0 or bm > 0 or bd > 0:
            set_status(s, "WARN")
            s["details"].append("이상 합계: pre_2020={0}, month_invalid={1}, day_invalid={2}".format(p, bm, bd))
        sections.append(s)

        # D-3
        s = sec("D-3", "etl_trade_raw_log 정합성")
        need = {"trade_type", "status", "row_count"}
        if not need.issubset(set(log_cols)):
            set_status(s, "FAIL")
            s["details"].append("etl_trade_raw_log 컬럼 부족: {0}".format(sorted(need - set(log_cols))))
        else:
            lrows = conn.execute("SELECT trade_type, COALESCE(SUM(row_count),0) fetched FROM etl_trade_raw_log WHERE status='OK' GROUP BY trade_type").fetchall()
            lmap = {r["trade_type"]: r["fetched"] for r in lrows}
            all_types = sorted(set(tcnt.keys()) | set(lmap.keys()))
            s["details"].append("trade_type | etl_ok_sum | fact_count | diff(etl-fact)")
            diff_any = False
            for t in all_types:
                e, f = (lmap.get(t, 0) or 0), (tcnt.get(t, 0) or 0)
                d = e - f
                if d != 0:
                    diff_any = True
                s["details"].append("{0} | {1} | {2} | {3}".format(t, e, f, d))
            if diff_any:
                set_status(s, "WARN")
                dmap = {}
                if "dedup_key" in fset:
                    dup_rows = conn.execute(
                        "SELECT trade_type, COALESCE(SUM(cnt-1),0) dup_rows FROM ("
                        "SELECT trade_type, dedup_key, COUNT(*) cnt FROM fact_trade_raw GROUP BY trade_type, dedup_key HAVING COUNT(*)>1"
                        ") GROUP BY trade_type"
                    ).fetchall()
                    dmap = {r["trade_type"]: r["dup_rows"] for r in dup_rows}
                else:
                    s["details"].append("참고: dedup_key 컬럼 부재로 dedup 기반 차이 추정은 생략")
                s["details"].append("차이 원인 추정:")
                for t in all_types:
                    e, f = (lmap.get(t, 0) or 0), (tcnt.get(t, 0) or 0)
                    d = e - f
                    if d == 0:
                        continue
                    reason = "ETL OK 합계가 큼(재수집/중복호출 후 dedup 가능)" if d > 0 else "fact 건수가 큼(로그 누락/기준상태 차이 가능)"
                    s["details"].append("- {0}: diff={1}, fact내 dedup_key중복행={2}, 추정={3}".format(t, d, dmap.get(t, 0) or 0, reason))
        sections.append(s)

        # E-1
        s = sec("E-1", "sgg_cd 형식 검사(5자리 숫자)")
        if "sgg_cd" not in fset:
            set_status(s, "FAIL")
            s["details"].append("sgg_cd 컬럼 없음")
        else:
            rows = conn.execute(
                "SELECT trade_type, "
                "SUM(CASE WHEN sgg_cd IS NULL OR CAST(sgg_cd AS TEXT)='' THEN 1 ELSE 0 END) AS null_blank, "
                "SUM(CASE WHEN sgg_cd IS NOT NULL AND CAST(sgg_cd AS TEXT)!='' AND (LENGTH(CAST(sgg_cd AS TEXT))!=5 OR only_digits(sgg_cd)=0) THEN 1 ELSE 0 END) AS bad "
                "FROM fact_trade_raw GROUP BY trade_type ORDER BY trade_type"
            ).fetchall()
            bad_total = 0
            for ln in rows_to_lines(rows, ["trade_type", "null_or_blank", "invalid_format"]):
                s["details"].append(ln)
            for r in rows:
                bad_total += r["bad"] or 0
            if bad_total > 0:
                set_status(s, "WARN")
                smp = conn.execute(
                    "SELECT trade_type, deal_year, deal_month, sgg_cd FROM fact_trade_raw "
                    "WHERE sgg_cd IS NOT NULL AND CAST(sgg_cd AS TEXT)!='' AND (LENGTH(CAST(sgg_cd AS TEXT))!=5 OR only_digits(sgg_cd)=0) LIMIT 5"
                ).fetchall()
                for ln in rows_to_lines(smp, ["trade_type", "deal_year", "deal_month", "sgg_cd"]):
                    s["details"].append(ln)
        sections.append(s)

        # E-2
        s = sec("E-2", "created_at / updated_at 타임스탬프 형식 검사")
        if not {"created_at", "updated_at"}.issubset(fset):
            set_status(s, "FAIL")
            s["details"].append("created_at/updated_at 컬럼 없음")
        else:
            rows = conn.execute(
                "SELECT trade_type, "
                "SUM(CASE WHEN created_at IS NULL OR CAST(created_at AS TEXT)='' THEN 1 ELSE 0 END) AS c_null, "
                "SUM(CASE WHEN updated_at IS NULL OR CAST(updated_at AS TEXT)='' THEN 1 ELSE 0 END) AS u_null, "
                "SUM(CASE WHEN created_at IS NOT NULL AND CAST(created_at AS TEXT)!='' AND is_ts(created_at)=0 THEN 1 ELSE 0 END) AS c_bad, "
                "SUM(CASE WHEN updated_at IS NOT NULL AND CAST(updated_at AS TEXT)!='' AND is_ts(updated_at)=0 THEN 1 ELSE 0 END) AS u_bad "
                "FROM fact_trade_raw GROUP BY trade_type ORDER BY trade_type"
            ).fetchall()
            bad_total = 0
            for ln in rows_to_lines(rows, ["trade_type", "created_null", "updated_null", "created_bad_format", "updated_bad_format"]):
                s["details"].append(ln)
            for r in rows:
                bad_total += (r["c_bad"] or 0) + (r["u_bad"] or 0)
            if bad_total > 0:
                set_status(s, "WARN")
                smp = conn.execute(
                    "SELECT trade_type, created_at, updated_at FROM fact_trade_raw "
                    "WHERE (created_at IS NOT NULL AND CAST(created_at AS TEXT)!='' AND is_ts(created_at)=0) "
                    "OR (updated_at IS NOT NULL AND CAST(updated_at AS TEXT)!='' AND is_ts(updated_at)=0) LIMIT 5"
                ).fetchall()
                for ln in rows_to_lines(smp, ["trade_type", "created_at", "updated_at"]):
                    s["details"].append(ln)
        sections.append(s)

        for s in sections:
            emit(logger, s)
            summary[s["status"]] += 1

        logger.line("========================================")
        logger.line("종합: PASS {0}건 / WARN {1}건 / FAIL {2}건".format(summary["PASS"], summary["WARN"], summary["FAIL"]))
        logger.line("========================================")

        target = os.path.join("scripts", "verify_trade_raw.py")
        if os.path.exists(target):
            py_compile.compile(target, doraise=True)
            logger.line("py_compile: OK ({0})".format(target))
        else:
            py_compile.compile(os.path.abspath(__file__), doraise=True)
            logger.line("py_compile: OK ({0})".format(os.path.abspath(__file__)))
        return 0
    except Exception as e:
        logger.line("")
        logger.line("[SYSTEM] 상태: FAIL")
        logger.line("오류: {0}".format(e))
        logger.line("========================================")
        logger.line("종합: PASS {0}건 / WARN {1}건 / FAIL {2}건".format(summary["PASS"], summary["WARN"], summary["FAIL"] + 1))
        logger.line("========================================")
        return 1
    finally:
        if conn is not None:
            conn.close()
        logger.close()


if __name__ == "__main__":
    sys.exit(run())
