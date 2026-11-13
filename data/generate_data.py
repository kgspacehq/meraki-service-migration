"""
Generate the fictional dataset for Meraki Service Migration & Release Readiness.

Simulated project. Meraki Industries and all data are fictional.
Not affiliated with Cisco Meraki.

Source of truth: docs/01-charter.md (waves, dates, depots, metrics).
Snapshot date: 2026-11-13.

Usage:  python data/generate_data.py
Writes the CSV files and data/meraki.db next to this script.
Uses only the Python standard library and a fixed seed, so output is reproducible.
"""
import csv
import os
import random
import sqlite3
from datetime import date, timedelta

random.seed(20261113)
HERE = os.path.dirname(os.path.abspath(__file__))
AS_OF = date(2026, 11, 13)
HISTORY_START = date(2023, 10, 1)          # ~3 years of service history (charter scope)
TARGET_LEGACY_TICKETS = 12000

# ---------------------------------------------------------------------------
# Waves (charter milestones). extract = legacy extract used for the migration
# load; migrated_at = load date; assessed = date of the go/no-go assessment.
# ---------------------------------------------------------------------------
WAVES = {
    1: dict(region="Southeast", planned=date(2026, 9, 25), actual=date(2026, 9, 25),
            extract=date(2026, 9, 25), migrated_at=date(2026, 9, 26), assessed=date(2026, 9, 23),
            recon_target=0.998, dup_rows=0, missing_open=0),
    2: dict(region="Northeast", planned=date(2026, 10, 23), actual=date(2026, 10, 23),
            extract=date(2026, 10, 23), migrated_at=date(2026, 10, 24), assessed=date(2026, 10, 21),
            recon_target=0.996, dup_rows=2, missing_open=0),
    3: dict(region="Midwest", planned=date(2026, 11, 20), actual=None,
            extract=date(2026, 11, 6), migrated_at=date(2026, 11, 7), assessed=AS_OF,
            recon_target=0.987, dup_rows=7, missing_open=4),       # dress-rehearsal load
    4: dict(region="West", planned=date(2026, 12, 18), actual=None,
            extract=AS_OF, migrated_at=None, assessed=AS_OF,
            recon_target=None, dup_rows=0, missing_open=0),        # not migrated yet
}

CITIES = {
    1: ["Miami", "Tampa", "Orlando", "Jacksonville", "Atlanta", "Charlotte", "Birmingham", "Nashville", "Raleigh", "Savannah"],
    2: ["Boston", "New York", "Newark", "Philadelphia", "Pittsburgh", "Baltimore", "Hartford", "Providence", "Albany", "Buffalo"],
    3: ["Chicago", "Detroit", "Cleveland", "Columbus", "Indianapolis", "Milwaukee", "Minneapolis", "St. Louis", "Kansas City", "Cincinnati"],
    4: ["Los Angeles", "San Diego", "San Jose", "Sacramento", "Phoenix", "Las Vegas", "Denver", "Salt Lake City", "Seattle", "Portland"],
}

OPEN_STATUSES = ("Open", "In Progress", "On Hold")
CLOSED_STATUSES = ("Closed", "Cancelled")


def d2s(d):
    return d.isoformat() if d else None


def rand_date(a, b):
    return a + timedelta(days=random.randint(0, (b - a).days))


def write_csv(name, header, rows):
    with open(os.path.join(HERE, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(["" if r[h] is None else r[h] for h in header])


# ---------------------------------------------------------------------------
# 1. Depots
# ---------------------------------------------------------------------------
depots = []
for wave, cities in CITIES.items():
    for i, city in enumerate(cities):
        n = (wave - 1) * 10 + i + 1
        depots.append(dict(
            depot_id=f"DEP-{n:02d}", depot_name=f"{city} Service Depot",
            region=WAVES[wave]["region"], wave=wave,
            planned_cutover_date=d2s(WAVES[wave]["planned"]),
            actual_cutover_date=d2s(WAVES[wave]["actual"]),
            technicians=random.randint(14, 38)))

# ---------------------------------------------------------------------------
# 2. Legacy tickets (extract per wave, see WAVES[...]["extract"])
# ---------------------------------------------------------------------------
customers = {w: [f"CUST-{(w - 1) * 450 + k:05d}" for k in range(1, 451)] for w in WAVES}
k_per_tech = TARGET_LEGACY_TICKETS / sum(d["technicians"] for d in depots)
legacy = []
for d in depots:
    wv = WAVES[d["wave"]]
    for _ in range(round(d["technicians"] * k_per_tech)):
        created = rand_date(HISTORY_START, wv["extract"])
        r = random.random()
        dur = int(random.expovariate(1 / 5)) if r < 0.85 else random.randint(15, 60) if r < 0.97 else random.randint(60, 150)
        closed = created + timedelta(days=dur)
        if closed <= wv["extract"]:
            status = "Cancelled" if random.random() < 0.03 else "Closed"
        else:
            status, closed = random.choices(OPEN_STATUSES, [0.35, 0.45, 0.20])[0], None
        legacy.append(dict(
            depot_id=d["depot_id"], wave=d["wave"], status=status,
            priority=random.choices(["P1", "P2", "P3", "P4"], [0.08, 0.22, 0.45, 0.25])[0],
            created_date=created, closed_date=closed,
            customer_id=None if random.random() < 0.015 else random.choice(customers[d["wave"]])))
legacy.sort(key=lambda t: (t["created_date"], t["depot_id"]))
for i, t in enumerate(legacy, 1):
    t["ticket_id"] = f"LT-{i:06d}"

# ---------------------------------------------------------------------------
# 3. Migrated tickets (Waves 1-3) with planted discrepancies
#    reconciled = migrated + same status + required dates present
# ---------------------------------------------------------------------------
migrated, planted = [], {}
for wave in (1, 2, 3):
    wv = WAVES[wave]
    tix = [t for t in legacy if t["wave"] == wave]
    n = len(tix)
    issues = n - round(n * wv["recon_target"])
    n_missing = round(issues * 0.45)
    n_mismatch = round(issues * 0.33)
    n_null = issues - n_missing - n_mismatch
    open_pool = [t for t in tix if t["status"] in OPEN_STATUSES]
    closed_pool = [t for t in tix if t["status"] in CLOSED_STATUSES]

    missing = random.sample(open_pool, wv["missing_open"])
    missing += random.sample([t for t in closed_pool if t not in missing], n_missing - wv["missing_open"])
    used = {t["ticket_id"] for t in missing}
    mismatch = random.sample([t for t in tix if t["ticket_id"] not in used], n_mismatch)
    used |= {t["ticket_id"] for t in mismatch}
    nulls = random.sample([t for t in closed_pool if t["ticket_id"] not in used], n_null)
    planted[wave] = dict(legacy=n, missing=len(missing), missing_open=wv["missing_open"],
                         mismatch=len(mismatch), nulls=len(nulls), dups=wv["dup_rows"])

    missing_ids = {t["ticket_id"] for t in missing}
    mismatch_ids = {t["ticket_id"] for t in mismatch}
    null_ids = {t["ticket_id"] for t in nulls}
    wave_rows = []
    for t in tix:
        if t["ticket_id"] in missing_ids:
            continue
        status, created, closed = t["status"], t["created_date"], t["closed_date"]
        if t["ticket_id"] in mismatch_ids:          # status mapping errors
            if status == "Closed":
                status = "Open"
            elif status == "Cancelled":
                status = "Closed"
            else:
                status, closed = "Closed", wv["migrated_at"]
        if t["ticket_id"] in null_ids:              # dates dropped during load
            if random.random() < 0.7:
                closed = None
            else:
                created = None
        wave_rows.append(dict(
            legacy_ticket_id=t["ticket_id"], depot_id=t["depot_id"], wave=wave, status=status,
            priority=t["priority"], created_date=created, closed_date=closed,
            customer_id=t["customer_id"], migrated_at=wv["migrated_at"]))
    clean_rows = [r for r in wave_rows if r["legacy_ticket_id"] not in mismatch_ids | null_ids]
    wave_rows += [dict(r) for r in random.sample(clean_rows, wv["dup_rows"])]   # duplicate loads
    migrated += wave_rows
for i, r in enumerate(migrated, 1):
    r["migrated_id"] = f"FS-{i:07d}"

# ---------------------------------------------------------------------------
# 4. Test cases (SIT + UAT per wave)
#    pass rate = Passed / (Passed + Failed); Blocked and Not Run are not executed
# ---------------------------------------------------------------------------
MODULES = ["Work Orders", "Dispatch & Scheduling", "Mobile App", "SLA Management",
           "Customer & Asset Data", "Data Migration", "ERP Billing Integration",
           "Parts Integration", "SSO & Access", "Reporting"]
TEST_PLAN = {  # (wave, type): (total, passed, failed, blocked, not_run, start, end)
    (1, "SIT"): (120, 116, 4, 0, 0, date(2026, 7, 20), date(2026, 8, 21)),
    (1, "UAT"): (200, 194, 6, 0, 0, date(2026, 8, 24), date(2026, 9, 18)),
    (2, "SIT"): (120, 115, 5, 0, 0, date(2026, 8, 31), date(2026, 9, 25)),
    (2, "UAT"): (200, 192, 7, 1, 0, date(2026, 9, 28), date(2026, 10, 16)),
    (3, "SIT"): (120, 115, 5, 0, 0, date(2026, 9, 28), date(2026, 10, 23)),
    (3, "UAT"): (200, 164, 16, 12, 8, date(2026, 10, 26), date(2026, 11, 13)),
    (4, "SIT"): (120, 22, 6, 2, 90, date(2026, 11, 2), date(2026, 11, 13)),
    (4, "UAT"): (200, 0, 0, 0, 200, None, None),
}
PROBLEM_MODULES = {3: {"Data Migration": 5, "ERP Billing Integration": 4}}
tests = []
for (wave, ttype), (total, p, f, b, nr, start, end) in TEST_PLAN.items():
    assert p + f + b + nr == total
    batch = [dict(test_id=f"TC-W{wave}-{ttype}-{k:03d}", wave=wave, test_type=ttype,
                  module=MODULES[(k - 1) % len(MODULES)], status="Passed") for k in range(1, total + 1)]
    weights = PROBLEM_MODULES.get(wave, {})
    pool = list(batch)
    for status, count in (("Failed", f), ("Blocked", b), ("Not Run", nr)):
        for _ in range(count):
            t = random.choices(pool, [weights.get(x["module"], 1) for x in pool])[0]
            t["status"] = status
            pool.remove(t)
    for t in batch:
        t["executed_date"] = d2s(rand_date(start, end)) if t["status"] in ("Passed", "Failed") else None
    tests += batch

# ---------------------------------------------------------------------------
# 5. Defects (~120)
# ---------------------------------------------------------------------------
TITLES = {
    "Work Orders": ["Work order cannot be reassigned after parts request", "Duplicate work order created on save"],
    "Dispatch & Scheduling": ["Technician calendar ignores depot time zone", "Auto-dispatch skips on-call technicians"],
    "Mobile App": ["Offline sync loses photos on reconnect", "Signature capture fails on older tablets"],
    "SLA Management": ["SLA clock does not pause when ticket is On Hold", "P1 escalation email not sent"],
    "Customer & Asset Data": ["Asset serial numbers truncated at 20 characters", "Customer contact missing on site record"],
    "Data Migration": ["Legacy status code not mapped", "Closed date dropped for tickets closed on weekends"],
    "ERP Billing Integration": ["Labor hours rounded incorrectly on invoice", "Billing message rejected for customers without tax ID"],
    "Parts Integration": ["Parts reservation not released on cancellation", "Stock level sync delayed by 2 hours"],
    "SSO & Access": ["Depot supervisor role can edit closed tickets", "SSO session expires during long site visits"],
    "Reporting": ["First-time-fix KPI counts cancelled tickets", "Depot dashboard filter returns all regions"],
}
DEFECT_PLAN = {  # wave: list of (severity, closed_count, open_count, deferred_count)
    1: [("S1", 2, 0, 0), ("S2", 6, 0, 0), ("S3", 12, 0, 0), ("S4", 6, 0, 2)],
    2: [("S1", 2, 0, 0), ("S2", 7, 0, 0), ("S3", 12, 1, 0), ("S4", 7, 0, 2)],
    3: [("S1", 3, 2, 0), ("S2", 8, 2, 0), ("S3", 12, 6, 0), ("S4", 8, 5, 0)],
    4: [("S1", 0, 1, 0), ("S2", 0, 3, 0), ("S3", 2, 4, 0), ("S4", 0, 5, 0)],
}
DEFECT_WINDOWS = {  # wave: (open_from, open_to, s1s2_close_by)
    1: (date(2026, 7, 20), date(2026, 9, 18), date(2026, 9, 21)),
    2: (date(2026, 8, 31), date(2026, 10, 16), date(2026, 10, 19)),
    3: (date(2026, 9, 28), date(2026, 11, 12), None),
    4: (date(2026, 11, 2), date(2026, 11, 12), None),
}
defects = []
for wave, plan in DEFECT_PLAN.items():
    lo, hi, close_by = DEFECT_WINDOWS[wave]
    for sev, n_closed, n_open, n_def in plan:
        for _ in range(n_closed):
            if sev in ("S1", "S2") and close_by:
                opened = rand_date(lo, close_by - timedelta(days=11))
                closed = min(opened + timedelta(days=random.randint(1, 10)), close_by)
            else:
                latest = {3: AS_OF - timedelta(days=13), 4: AS_OF - timedelta(days=5)}.get(wave, hi)
                opened = rand_date(lo, min(hi, latest))
                closed = min(opened + timedelta(days=random.randint(1, 12)), AS_OF - timedelta(days=1))
            mod = random.choice(MODULES)
            defects.append(dict(wave=wave, severity=sev, status="Closed", module=mod,
                                title=random.choice(TITLES[mod]), opened_date=opened, closed_date=closed))
        for _ in range(n_def):
            mod = random.choice(MODULES)
            defects.append(dict(wave=wave, severity=sev, status="Deferred", module=mod,
                                title=random.choice(TITLES[mod]), opened_date=rand_date(lo, hi), closed_date=None))
        for _ in range(n_open):
            mod = random.choice(MODULES)
            if wave == 2:   # hypercare defect raised after go-live
                opened = date(2026, 10, 28)
            else:
                opened = rand_date(max(lo, date(2026, 10, 15)), hi)
            defects.append(dict(wave=wave, severity=sev, module=mod, title=random.choice(TITLES[mod]),
                                status=random.choice(["Open", "In Progress", "Fixed - Retest"]),
                                opened_date=opened, closed_date=None))
# The two Wave 3 blockers are written explicitly so the story is clear.
w3_s1 = [x for x in defects if x["wave"] == 3 and x["severity"] == "S1" and x["closed_date"] is None]
w3_s1[0].update(module="Data Migration", status="In Progress", opened_date=date(2026, 11, 4),
                title="Open tickets dropped when legacy depot code has a trailing space")
w3_s1[1].update(module="ERP Billing Integration", status="Open", opened_date=date(2026, 11, 9),
                title="Invoices not created for work orders closed after migration")
defects.sort(key=lambda x: (x["opened_date"], x["wave"], x["severity"]))
for i, x in enumerate(defects, 1):
    x["defect_id"] = f"DEF-{i:03d}"

# ---------------------------------------------------------------------------
# 6. Readiness criteria (12 per wave). Data-driven criteria are computed from
#    the generated data with the same definitions used in /sql.
# ---------------------------------------------------------------------------
def pass_rate(wave, ttype):
    ex = [t for t in tests if t["wave"] == wave and t["test_type"] == ttype and t["status"] in ("Passed", "Failed")]
    return round(100 * sum(t["status"] == "Passed" for t in ex) / len(ex), 1) if ex else None


def open_defects(wave, sev, on):
    return sum(1 for x in defects if x["wave"] == wave and x["severity"] == sev and x["status"] != "Deferred"
               and x["opened_date"] <= on and (x["closed_date"] is None or x["closed_date"] > on))


def reconciliation(wave):
    rows = [r for r in migrated if r["wave"] == wave]
    if not rows:
        return None, None
    by_id = {}
    for r in rows:
        by_id.setdefault(r["legacy_ticket_id"], []).append(r)
    tix = [t for t in legacy if t["wave"] == wave]
    ok = lost_open = 0
    for t in tix:
        ms = by_id.get(t["ticket_id"], [])
        if not ms and t["status"] in OPEN_STATUSES:
            lost_open += 1
        if any(m["status"] == t["status"] and m["created_date"] is not None and
               (m["status"] not in CLOSED_STATUSES or m["closed_date"] is not None) for m in ms):
            ok += 1
    return round(100 * ok / len(tix), 1), lost_open


MANUAL = {  # criteria tracked outside the data: rehearsal downtime, rollback, training, super-users, security, hypercare
    1: dict(C07=3.1, C08=1, C09=96, C10=2.6, C11=1, C12=100),
    2: dict(C07=3.4, C08=1, C09=94, C10=2.4, C11=1, C12=100),
    3: dict(C07=3.6, C08=1, C09=92, C10=2.2, C11=1, C12=100),
    4: dict(C07=None, C08=0, C09=18, C10=1.2, C11=0, C12=40),
}
CRITERIA = [  # id, criterion, category, weight, comparator, threshold, unit, gate, floor
    ("C01", "UAT pass rate", "Testing", 12, ">=", 95, "%", "Y", 85),
    ("C02", "SIT pass rate", "Testing", 6, ">=", 95, "%", "N", 85),
    ("C03", "Open S1 defects", "Quality", 12, "<=", 0, "count", "Y", None),
    ("C04", "Open S2 defects", "Quality", 8, "<=", 2, "count", "N", None),
    ("C05", "Ticket reconciliation rate", "Data", 12, ">=", 99.5, "%", "Y", 97.5),
    ("C06", "Open tickets lost in migration", "Data", 10, "<=", 0, "count", "Y", None),
    ("C07", "Cutover rehearsal downtime per depot", "Cutover", 8, "<=", 4, "hours", "N", None),
    ("C08", "Rollback plan approved", "Cutover", 6, "=", 1, "flag", "N", None),
    ("C09", "End users trained", "People", 8, ">=", 90, "%", "N", 70),
    ("C10", "Super-users per depot (average)", "People", 4, ">=", 2, "count", "N", 1),
    ("C11", "Security access review signed off", "Security", 8, "=", 1, "flag", "N", None),
    ("C12", "Hypercare roster staffed", "Support", 6, ">=", 100, "%", "N", 50),
]
assert sum(c[3] for c in CRITERIA) == 100


def score(comp, thr, act, floor):
    """100 if met; otherwise partial credit (linear from floor for >=, -50 per unit over for <=)."""
    if act is None:
        return 0, "N"
    met = act >= thr if comp == ">=" else act <= thr if comp == "<=" else act == thr
    if met:
        return 100, "Y"
    if comp == ">=" and floor is not None:
        return round(max(0, (act - floor) / (thr - floor) * 100)), "N"
    if comp == "<=":
        return round(max(0, 100 - 50 * (act - thr))), "N"
    return 0, "N"


readiness = []
for wave, wv in WAVES.items():
    on = wv["assessed"]
    recon, lost = reconciliation(wave)
    actual = dict(C01=pass_rate(wave, "UAT"), C02=pass_rate(wave, "SIT"),
                  C03=open_defects(wave, "S1", on), C04=open_defects(wave, "S2", on),
                  C05=recon, C06=lost, **MANUAL[wave])
    for cid, name, cat, wt, comp, thr, unit, gate, floor in CRITERIA:
        s, met = score(comp, thr, actual[cid], floor)
        readiness.append(dict(wave=wave, criterion_id=cid, criterion=name, category=cat, weight=wt,
                              comparator=comp, threshold=thr, unit=unit, actual_value=actual[cid],
                              score=s, met=met, gate=gate, assessed_date=d2s(on)))

# ---------------------------------------------------------------------------
# 7. Risks (aligned with the charter)
# ---------------------------------------------------------------------------
risks = [
    ("R-01", "Poor legacy data quality slows migration and lowers reconciliation", 5, 4, "Michelle Park", "Mitigate: data profiling and cleansing sprint before each wave, depot data owners", "Occurred"),
    ("R-02", "Integration with the legacy ERP fails at cutover (billing, parts)", 4, 5, "Priya Raman", "Mitigate: end-to-end integration tests every sprint, cutover rehearsal per wave", "Open"),
    ("R-03", "Open tickets lost or corrupted during migration", 3, 5, "James Whitfield", "Avoid: reconciliation gate at 99.5% and 0 open tickets lost before go-live", "Open"),
    ("R-04", "Technicians resist the new mobile app", 3, 3, "Robert Hayes", "Mitigate: 2+ super-users per depot, hands-on training, floor support in hypercare", "Open"),
    ("R-05", "Vendor resourcing gaps during overlapping waves", 2, 3, "Keren", "Mitigate: named resources in the SOW, escalation path to vendor account lead", "Open"),
    ("R-06", "Wave 4 overlaps the holiday period; Wave 3 slip compresses Wave 4", 4, 4, "Keren", "Mitigate: fixed Dec 18 deadline, buffer week, re-plan if Wave 3 is NO-GO", "Open"),
    ("R-07", "Cutover downtime exceeds 4 hours per depot", 2, 4, "Priya Raman", "Mitigate: timed rehearsals, parallel load, rollback trigger at 3.5 hours", "Open"),
    ("R-08", "Security rejects SSO or data-residency model", 2, 4, "Marcus Bell", "Avoid: security review gate before Wave 1", "Closed"),
    ("R-09", "Unsupported legacy system fails before decommissioning", 2, 5, "Priya Raman", "Accept with contingency: nightly read-only backup, vendor-independent DB access", "Open"),
    ("R-10", "Budget overrun from extra cleansing sprints and Wave 3 re-test", 3, 3, "Keren", "Mitigate: draw from 10% contingency, monthly review with Finance", "Open"),
    ("R-11", "Depot key users unavailable for UAT during peak season", 3, 3, "Ana Morales", "Mitigate: book UAT slots 4 weeks ahead, backup key users per depot", "Occurred"),
    ("R-12", "Billing errors after go-live delay the financial close", 2, 4, "Sofia Delgado", "Mitigate: billing reconciliation in hypercare, finance sign-off on integration tests", "Open"),
]
risks = [dict(risk_id=r[0], description=r[1], probability=r[2], impact=r[3], owner=r[4], response=r[5], status=r[6]) for r in risks]

# ---------------------------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------------------------
for t in legacy:
    t["created_date"], t["closed_date"] = d2s(t["created_date"]), d2s(t["closed_date"])
for r in migrated:
    r["created_date"], r["closed_date"], r["migrated_at"] = d2s(r["created_date"]), d2s(r["closed_date"]), d2s(r["migrated_at"])
for x in defects:
    x["opened_date"], x["closed_date"] = d2s(x["opened_date"]), d2s(x["closed_date"])

TABLES = {
    "depots": (["depot_id", "depot_name", "region", "wave", "planned_cutover_date", "actual_cutover_date", "technicians"], depots),
    "legacy_tickets": (["ticket_id", "depot_id", "status", "priority", "created_date", "closed_date", "customer_id"], legacy),
    "migrated_tickets": (["migrated_id", "legacy_ticket_id", "depot_id", "wave", "status", "priority", "created_date", "closed_date", "customer_id", "migrated_at"], migrated),
    "test_cases": (["test_id", "wave", "test_type", "module", "status", "executed_date"], tests),
    "defects": (["defect_id", "wave", "severity", "status", "module", "title", "opened_date", "closed_date"], defects),
    "readiness_criteria": (["wave", "criterion_id", "criterion", "category", "weight", "comparator", "threshold", "unit", "actual_value", "score", "met", "gate", "assessed_date"], readiness),
    "risks": (["risk_id", "description", "probability", "impact", "owner", "response", "status"], risks),
}
for name, (header, rows) in TABLES.items():
    write_csv(f"{name}.csv", header, rows)

# ---------------------------------------------------------------------------
# Build SQLite database
# ---------------------------------------------------------------------------
DDL = """
CREATE TABLE depots (
    depot_id TEXT PRIMARY KEY, depot_name TEXT NOT NULL, region TEXT NOT NULL,
    wave INTEGER NOT NULL, planned_cutover_date TEXT NOT NULL, actual_cutover_date TEXT,
    technicians INTEGER NOT NULL);
CREATE TABLE legacy_tickets (
    ticket_id TEXT PRIMARY KEY, depot_id TEXT NOT NULL REFERENCES depots(depot_id),
    status TEXT NOT NULL, priority TEXT NOT NULL, created_date TEXT NOT NULL,
    closed_date TEXT, customer_id TEXT);
CREATE TABLE migrated_tickets (
    migrated_id TEXT PRIMARY KEY, legacy_ticket_id TEXT NOT NULL, depot_id TEXT NOT NULL,
    wave INTEGER NOT NULL, status TEXT, priority TEXT, created_date TEXT, closed_date TEXT,
    customer_id TEXT, migrated_at TEXT NOT NULL);
CREATE TABLE test_cases (
    test_id TEXT PRIMARY KEY, wave INTEGER NOT NULL, test_type TEXT NOT NULL,
    module TEXT NOT NULL, status TEXT NOT NULL, executed_date TEXT);
CREATE TABLE defects (
    defect_id TEXT PRIMARY KEY, wave INTEGER NOT NULL, severity TEXT NOT NULL,
    status TEXT NOT NULL, module TEXT NOT NULL, title TEXT NOT NULL,
    opened_date TEXT NOT NULL, closed_date TEXT);
CREATE TABLE readiness_criteria (
    wave INTEGER NOT NULL, criterion_id TEXT NOT NULL, criterion TEXT NOT NULL,
    category TEXT NOT NULL, weight INTEGER NOT NULL, comparator TEXT NOT NULL,
    threshold REAL NOT NULL, unit TEXT NOT NULL, actual_value REAL, score INTEGER NOT NULL,
    met TEXT NOT NULL, gate TEXT NOT NULL, assessed_date TEXT NOT NULL,
    PRIMARY KEY (wave, criterion_id));
CREATE TABLE risks (
    risk_id TEXT PRIMARY KEY, description TEXT NOT NULL, probability INTEGER NOT NULL,
    impact INTEGER NOT NULL, owner TEXT NOT NULL, response TEXT NOT NULL, status TEXT NOT NULL);
CREATE INDEX ix_legacy_depot ON legacy_tickets(depot_id);
CREATE INDEX ix_migrated_legacy ON migrated_tickets(legacy_ticket_id);
"""
db_path = os.path.join(HERE, "meraki.db")
if os.path.exists(db_path):
    os.remove(db_path)
con = sqlite3.connect(db_path)
con.executescript(DDL)
for name, (header, rows) in TABLES.items():
    con.executemany(f"INSERT INTO {name} ({','.join(header)}) VALUES ({','.join('?' * len(header))})",
                    [[r[h] for h in header] for r in rows])
con.commit()
con.close()

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"legacy_tickets={len(legacy)} migrated_rows={len(migrated)} tests={len(tests)} defects={len(defects)}")
for w, p in planted.items():
    print(f"wave {w} planted: {p}")
for w in WAVES:
    rows = [r for r in readiness if r["wave"] == w]
    print(f"wave {w} weighted score: {sum(r['weight'] * r['score'] for r in rows) / 100:.1f}")
