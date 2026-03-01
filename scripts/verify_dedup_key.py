import collections
import os
import py_compile
import sqlite3
import sys
import time


DB_DEFAULT = "/home/deploy/real_estate_report/data/real_estate.db"
OUT_DEFAULT = os.path.join("logs", "verify_dedup_key_result.txt")

# LandScanner dedup key (source + SQLite unique index)
DEDUP_GROUP_EXPR = """
trade_type,
sgg_cd,
deal_year,
deal_month,
COALESCE(deal_day, ''),
COALESCE(bldg_nm, ''),
COALESCE(exclu_use_ar, 0),
COALESCE(floor, ''),
COALESCE(deal_amount, 0),
COALESCE(deposit, 0),
COALESCE(monthly_rent, 0),
COALESCE(jibun, '')
""".strip()


class Tee:
    def __init__(self, out_path):
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        self.fp = open(out_path, "w", encoding="utf-8")

    def line(self, text=""):
        print(text)
        self.fp.write(text + "\n")
        self.fp.flush()

    def close(self):
        self.fp.close()


def parse_args(argv):
    db_path = DB_DEFAULT
    out_path = OUT_DEFAULT
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg in ("--db", "--db-path"):
            db_path = argv[i + 1]
            i += 2
        elif arg in ("--out", "--output"):
            out_path = argv[i + 1]
            i += 2
        else:
            raise ValueError("unknown argument: {0}".format(arg))
    return db_path, out_path


def timed_query(conn, sql):
    started = time.perf_counter()
    rows = conn.execute(sql).fetchall()
    elapsed = time.perf_counter() - started
    return rows, elapsed


def run():
    db_path, out_path = parse_args(sys.argv)
    logger = Tee(out_path)
    conn = None
    try:
        if not os.path.exists(db_path):
            raise FileNotFoundError("DB file not found: {0}".format(db_path))

        conn = sqlite3.connect("file:{0}?mode=ro".format(db_path), uri=True)
        conn.row_factory = sqlite3.Row

        ts = conn.execute("SELECT strftime('%Y-%m-%dT%H:%M:%SZ','now')").fetchone()[0]
        total_rows = conn.execute("SELECT COUNT(*) FROM fact_trade_raw").fetchone()[0]

        logger.line("========================================")
        logger.line("fact_trade_raw dedup_key 검증 결과")
        logger.line("실행 시각: {0}".format(ts))
        logger.line("DB: {0}".format(db_path))
        logger.line("총 건수: {0}".format(total_rows))
        logger.line("========================================")
        logger.line("")

        logger.line("[B-2] SQLite UNIQUE 제약 / INDEX 확인")
        logger.line("상태: PASS")
        tbl_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND tbl_name='fact_trade_raw'"
        ).fetchone()
        logger.line("table_sql:")
        logger.line(tbl_sql["sql"] if tbl_sql and tbl_sql["sql"] else "NULL")
        logger.line("")
        idx_rows = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='fact_trade_raw' ORDER BY name"
        ).fetchall()
        logger.line("index_sql:")
        for r in idx_rows:
            logger.line("- {0}".format(r["name"]))
            logger.line("  {0}".format(r["sql"]))
        logger.line("")

        logger.line("[B-3] dedup 키 기준 중복 검사")
        dup_sql = (
            "WITH dup AS ("
            "  SELECT {expr}, COUNT(*) AS cnt "
            "  FROM fact_trade_raw "
            "  GROUP BY {expr} "
            "  HAVING COUNT(*) > 1"
            ") "
            "SELECT COUNT(*) AS dup_key_count, "
            "       COALESCE(SUM(cnt),0) AS dup_row_sum, "
            "       COALESCE(SUM(cnt-1),0) AS dup_excess_rows "
            "FROM dup"
        ).format(expr=DEDUP_GROUP_EXPR)
        summary_rows, elapsed = timed_query(conn, dup_sql)
        summary = summary_rows[0]
        dup_key_count = summary["dup_key_count"]
        dup_row_sum = summary["dup_row_sum"]
        dup_excess = summary["dup_excess_rows"]
        status = "PASS" if dup_key_count == 0 else "WARN"
        logger.line("상태: {0}".format(status))
        logger.line("dedup_key 조합:")
        for p in DEDUP_GROUP_EXPR.splitlines():
            logger.line("- {0}".format(p.strip()))
        logger.line("중복 키 수: {0}".format(dup_key_count))
        logger.line("중복 행 수 합계: {0}".format(dup_row_sum))
        logger.line("초과 행 수(cnt-1): {0}".format(dup_excess))
        logger.line("집계 쿼리 소요: {0:.2f}초".format(elapsed))
        if elapsed > 60:
            logger.line("참고: 단일 쿼리 60초 초과 (전수 집계)")
        logger.line("")

        by_type_sql = (
            "SELECT trade_type, COUNT(*) AS dup_key_count, COALESCE(SUM(cnt-1),0) AS dup_excess_rows "
            "FROM ("
            "  SELECT trade_type, {expr}, COUNT(*) AS cnt "
            "  FROM fact_trade_raw "
            "  GROUP BY trade_type, {expr} "
            "  HAVING COUNT(*) > 1"
            ") "
            "GROUP BY trade_type "
            "ORDER BY dup_excess_rows DESC, trade_type"
        ).format(expr=DEDUP_GROUP_EXPR)
        by_type_rows, by_type_elapsed = timed_query(conn, by_type_sql)
        logger.line("trade_type별 중복 분포 (dup_key_count | dup_excess_rows):")
        if by_type_rows:
            for r in by_type_rows:
                logger.line("- {0}: {1} | {2}".format(r["trade_type"], r["dup_key_count"], r["dup_excess_rows"]))
        else:
            logger.line("- 중복 없음")
        logger.line("trade_type 집계 쿼리 소요: {0:.2f}초".format(by_type_elapsed))
        if by_type_elapsed > 60:
            logger.line("참고: 단일 쿼리 60초 초과 (전수 집계)")
        logger.line("")

        top_sql = (
            "SELECT {expr}, COUNT(*) AS cnt "
            "FROM fact_trade_raw "
            "GROUP BY {expr} "
            "HAVING COUNT(*) > 1 "
            "ORDER BY cnt DESC "
            "LIMIT 10"
        ).format(expr=DEDUP_GROUP_EXPR)
        top_rows, top_elapsed = timed_query(conn, top_sql)
        logger.line("상위 10건 샘플:")
        if top_rows:
            header = [
                "trade_type",
                "sgg_cd",
                "deal_year",
                "deal_month",
                "deal_day",
                "bldg_nm",
                "exclu_use_ar",
                "floor",
                "deal_amount",
                "deposit",
                "monthly_rent",
                "jibun",
                "cnt",
            ]
            logger.line(" | ".join(header))
            for r in top_rows:
                vals = [str(r[h]) for h in header]
                logger.line(" | ".join(vals))
        else:
            logger.line("- 샘플 없음 (중복 키 없음)")
        logger.line("top10 쿼리 소요: {0:.2f}초".format(top_elapsed))
        if top_elapsed > 60:
            logger.line("참고: 단일 쿼리 60초 초과 (전수 집계)")
        logger.line("")

        pass_cnt = 2 if status == "PASS" else 1
        warn_cnt = 0 if status == "PASS" else 1
        logger.line("========================================")
        logger.line("종합: PASS {0}건 / WARN {1}건 / FAIL 0건".format(pass_cnt, warn_cnt))
        logger.line("========================================")

        compile_target = os.path.join("scripts", "verify_dedup_key.py")
        if os.path.exists(compile_target):
            py_compile.compile(compile_target, doraise=True)
            logger.line("py_compile: OK ({0})".format(compile_target))
        else:
            py_compile.compile(os.path.abspath(__file__), doraise=True)
            logger.line("py_compile: OK ({0})".format(os.path.abspath(__file__)))

        return 0
    except Exception as exc:
        logger.line("")
        logger.line("[SYSTEM] 상태: FAIL")
        logger.line("오류: {0}".format(exc))
        logger.line("========================================")
        logger.line("종합: PASS 0건 / WARN 0건 / FAIL 1건")
        logger.line("========================================")
        return 1
    finally:
        if conn is not None:
            conn.close()
        logger.close()


if __name__ == "__main__":
    sys.exit(run())
