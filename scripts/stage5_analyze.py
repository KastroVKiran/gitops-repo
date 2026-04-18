#!/usr/bin/env python3
"""
================================================================
STAGE 5: STATISTICAL ANALYSIS
================================================================
Run AFTER stage4_experiments.py has finished.
Reads all CSV files and computes all statistics needed
for the IEEE paper tables and text.

HOW TO RUN:
  python3 scripts/stage5_analyze.py

OUTPUT:
  Prints all paper-ready statistics to terminal
  Saves outputs/paper_statistics.txt
================================================================
"""

import csv, statistics, math
from pathlib import Path
from collections import defaultdict

OUT = Path("outputs")

def load(fname):
    path = OUT / fname
    if not path.exists():
        print(f"  WARNING: {fname} not found. Run stage4 first.")
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def flt(rows, col, filter_col=None, filter_val=None):
    result = []
    for r in rows:
        if filter_col and str(r.get(filter_col,"")) != str(filter_val):
            continue
        try:
            v = float(r[col])
            if v > 0:
                result.append(v)
        except Exception:
            pass
    return result

def stats(vals):
    if not vals:
        return 0,0,0,0
    n = len(vals)
    m = statistics.mean(vals)
    s = statistics.stdev(vals) if n > 1 else 0
    return round(m,4), round(s,4), round(min(vals),4), round(max(vals),4)

def ci95(vals):
    n = len(vals)
    m = statistics.mean(vals)
    s = statistics.stdev(vals) if n > 1 else 0
    margin = 1.96 * s / math.sqrt(n)
    return round(m - margin, 4), round(m + margin, 4)

def welch_t(a, b):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return 0, 0, 1.0
    ma, mb = statistics.mean(a), statistics.mean(b)
    va = statistics.variance(a) / na
    vb = statistics.variance(b) / nb
    se = math.sqrt(va + vb)
    if se == 0:
        return 0, 0, 1.0
    t = (ma - mb) / se
    df = (va + vb)**2 / (
        (va**2 / (na-1)) + (vb**2 / (nb-1))
    )
    # p-value: two-tailed using normal approx for |t| > 2
    p = 2 * (1 - _ncdf(abs(t)))
    return round(t,4), round(df,2), round(p,8)

def cohens_d(a, b):
    if len(a) < 2 or len(b) < 2:
        return 0
    pooled = math.sqrt((statistics.variance(a) + statistics.variance(b)) / 2)
    return round(abs(statistics.mean(a) - statistics.mean(b)) / pooled, 4) if pooled else 0

def mann_whitney(a, b):
    n1, n2 = len(a), len(b)
    combined = sorted([(v,'a') for v in a] + [(v,'b') for v in b])
    ranks_a = []
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            if combined[k][1] == 'a':
                ranks_a.append(avg_rank)
        i = j
    u1 = sum(ranks_a) - n1*(n1+1)/2
    u2 = n1*n2 - u1
    u  = min(u1, u2)
    mu_u = n1*n2/2
    sig  = math.sqrt(n1*n2*(n1+n2+1)/12)
    z    = (u - mu_u) / sig if sig else 0
    p    = 2*(1-_ncdf(abs(z)))
    return round(u,1), round(p,8)

def _ncdf(x):
    return 0.5*(1+math.erf(x/math.sqrt(2)))

def div(title):
    print("\n" + "="*65)
    print(f"  {title}")
    print("="*65)

def save_line(f, line):
    print(line)
    f.write(line + "\n")

def main():
    out_txt = OUT / "paper_statistics.txt"
    with open(out_txt, "w") as f:
        def p(line=""):
            save_line(f, line)

        p("="*65)
        p("  IEEE PAPER — STATISTICAL ANALYSIS RESULTS")
        p("="*65)

        # ── EXP 1: PROPOSED DEPLOYMENTS ──────────────────────────────
        p()
        p("EXPERIMENT 1 — PROPOSED FRAMEWORK DEPLOYMENTS")
        p("-"*65)
        e1 = load("exp1_proposed_deployments.csv")
        prop_all  = flt(e1, "total_min")
        prop_ok   = flt(e1, "total_min", "success", "True")
        failures1 = sum(1 for r in e1 if str(r.get("success","")) != "True")

        m,s,mn,mx = stats(prop_ok)
        ci = ci95(prop_ok)
        p(f"  N runs        : {len(e1)}")
        p(f"  Successful    : {len(prop_ok)}  Failed: {failures1}")
        p(f"  Mean ± SD     : {m} ± {s} min")
        p(f"  Median        : {round(statistics.median(prop_ok),4)} min")
        p(f"  Min – Max     : {mn} – {mx} min")
        p(f"  95% CI        : [{ci[0]}, {ci[1]}] min")
        p(f"  Failure rate  : {failures1}/{len(e1)} = {100*failures1/max(len(e1),1):.1f}%")

        if e1:
            builds  = flt(e1, "build_s")
            pushes  = flt(e1, "push_s")
            detects = flt(e1, "argocd_detect_s")
            syncs   = flt(e1, "argocd_sync_s")
            p(f"  -- Per-stage breakdown (proposed) --")
            p(f"  Build         : {round(statistics.mean(builds),2)} ± {round(statistics.stdev(builds) if len(builds)>1 else 0,2)} s")
            p(f"  Push          : {round(statistics.mean(pushes),2)} ± {round(statistics.stdev(pushes) if len(pushes)>1 else 0,2)} s")
            p(f"  Argo detect   : {round(statistics.mean(detects),2)} ± {round(statistics.stdev(detects) if len(detects)>1 else 0,2)} s")
            p(f"  Argo sync     : {round(statistics.mean(syncs),2)} ± {round(statistics.stdev(syncs) if len(syncs)>1 else 0,2)} s")
            webhook = sum(1 for r in e1 if r.get("detection_path","") == "webhook")
            p(f"  Detection path: {webhook} webhook, {len(e1)-webhook} polling")

        # ── EXP 2: BASELINE DEPLOYMENTS ──────────────────────────────
        p()
        p("EXPERIMENT 2 — BASELINE (kubectl) DEPLOYMENTS")
        p("-"*65)
        e2 = load("exp2_baseline_deployments.csv")
        base_all = flt(e2, "total_min")
        base_ok  = flt(e2, "total_min", "success", "True")
        failures2 = sum(1 for r in e2 if str(r.get("success","")) != "True")

        m2,s2,mn2,mx2 = stats(base_all)
        ci2 = ci95(base_all)
        p(f"  N runs        : {len(e2)}")
        p(f"  Successful    : {len(base_ok)}  Failed: {failures2}")
        p(f"  Op.Mean ± SD  : {m2} ± {s2} min  (all runs incl. failures)")
        p(f"  Median        : {round(statistics.median(base_all),4)} min")
        p(f"  Min – Max     : {mn2} – {mx2} min")
        p(f"  95% CI        : [{ci2[0]}, {ci2[1]}] min")
        p(f"  Failure rate  : {failures2}/{len(e2)} = {100*failures2/max(len(e2),1):.1f}%")
        if base_ok:
            m2s,s2s,_,_ = stats(base_ok)
            p(f"  Success-only  : {m2s} ± {s2s} min")

        # ── STATISTICAL TESTS: DEPLOYMENT ────────────────────────────
        p()
        p("STATISTICAL TESTS — DEPLOYMENT TIME")
        p("-"*65)
        if prop_ok and base_all:
            t,df,pv = welch_t(base_all, prop_ok)
            d  = cohens_d(base_all, prop_ok)
            U, pU = mann_whitney(base_all, prop_ok)
            pct = round(100*(statistics.mean(base_all)-statistics.mean(prop_ok))/statistics.mean(base_all),1)
            p(f"  H0: no difference in deployment time")
            p(f"  Welch t-test  : t({df}) = {t},  p = {pv}")
            p(f"  Cohen's d     : {d}  ({'large' if d>0.8 else 'medium' if d>0.5 else 'small'} effect)")
            p(f"  Mann-Whitney  : U = {U},  p = {pU}")
            p(f"  Reduction     : {pct}%  ({round(statistics.mean(base_all),4)} -> {round(statistics.mean(prop_ok),4)} min)")
            p(f"  Significance  : {'REJECTED H0 (p<0.05)' if pv < 0.05 else 'FAIL TO REJECT H0'}")
            if base_ok:
                t2,df2,pv2 = welch_t(base_ok, prop_ok)
                d2 = cohens_d(base_ok, prop_ok)
                p(f"  Success-only  : t({df2}) = {t2},  p = {pv2},  d = {d2}")

        # ── EXP 3: DRIFT CORRECTION ───────────────────────────────────
        p()
        p("EXPERIMENT 3 — DRIFT CORRECTION")
        p("-"*65)
        e3 = load("exp3_drift_correction.csv")
        det  = flt(e3, "detection_s")
        corr = flt(e3, "correction_s")
        tot  = flt(e3, "total_resolution_s")
        p(f"  N events      : {len(e3)}")
        if det:
            dm,ds,dmn,dmx = stats(det)
            cm,cs,cmn,cmx = stats(corr)
            tm,ts2,tmn,tmx = stats(tot)
            p(f"  Detection     : {dm} ± {ds} s   [{dmn} – {dmx}]")
            p(f"  Correction    : {cm} ± {cs} s   [{cmn} – {cmx}]")
            p(f"  Total Resol.  : {tm} ± {ts2} s   [{tmn} – {tmx}]")
            wh = sum(1 for r in e3 if r.get("detection_path","") == "webhook")
            p(f"  Detection path: {wh} webhook, {len(e3)-wh} polling")
            by_type = defaultdict(list)
            for r in e3:
                by_type[r.get("drift_type","")].append(float(r.get("total_resolution_s",0)))
            p(f"  By drift type:")
            for dt, vals in sorted(by_type.items()):
                p(f"    {dt:30s}: mean={round(statistics.mean(vals),2)}s  n={len(vals)}")

        # ── EXP 4: ROLLBACK ───────────────────────────────────────────
        p()
        p("EXPERIMENT 4 — ROLLBACK")
        p("-"*65)
        e4 = load("exp4_rollback.csv")
        prop_rb = flt(e4, "rollback_duration_min", "config", "proposed")
        base_rb = flt(e4, "rollback_duration_min", "config", "baseline")
        p(f"  N events (each): {len(prop_rb)} proposed, {len(base_rb)} baseline")
        if prop_rb and base_rb:
            pm,ps,pmn,pmx = stats(prop_rb)
            bm,bs,bmn,bmx = stats(base_rb)
            pci = ci95(prop_rb)
            bci = ci95(base_rb)
            p(f"  Proposed      : {pm} ± {ps} min   [{pmn} – {pmx}]")
            p(f"  Proposed 95%CI: [{pci[0]}, {pci[1]}] min")
            p(f"  Baseline      : {bm} ± {bs} min   [{bmn} – {bmx}]")
            p(f"  Baseline 95%CI: [{bci[0]}, {bci[1]}] min")
            t,df,pv = welch_t(base_rb, prop_rb)
            d  = cohens_d(base_rb, prop_rb)
            pct = round(100*(bm-pm)/bm, 1)
            p(f"  Welch t-test  : t({df}) = {t},  p = {pv}")
            p(f"  Cohen's d     : {d}  ({'large' if d>0.8 else 'medium' if d>0.5 else 'small'} effect)")
            p(f"  Reduction     : {pct}%  ({bm} -> {pm} min)")

        # ── EXP 5: CHAOS ──────────────────────────────────────────────
        p()
        p("EXPERIMENT 5 — CHAOS RESILIENCE (NOVEL)")
        p("-"*65)
        e5 = load("exp5_chaos_resilience.csv")
        rec  = flt(e5, "recovery_s")
        down = flt(e5, "downtime_s")
        errs = flt(e5, "http_errors")
        p(f"  N events      : {len(e5)}")
        if rec:
            rm,rs,rmn,rmx = stats(rec)
            dm,ds,dmn,dmx = stats(down)
            em,es,_,_     = stats(errs)
            p(f"  Recovery time : {rm} ± {rs} s   [{rmn} – {rmx}]")
            p(f"  Downtime      : {dm} ± {ds} s   [{dmn} – {dmx}]")
            p(f"  HTTP errors   : {em} ± {es} per event")
            by_type = defaultdict(list)
            for r in e5:
                by_type[r.get("chaos_type","")].append(float(r.get("recovery_s",0)))
            p(f"  By chaos type:")
            for ct, vals in sorted(by_type.items()):
                p(f"    {ct:35s}: mean={round(statistics.mean(vals),2)}s  n={len(vals)}")

        # ── EXP 6: HPA ────────────────────────────────────────────────
        p()
        p("EXPERIMENT 6 — HPA SCALING")
        p("-"*65)
        e6 = load("exp6_hpa_scaling.csv")
        by_load = defaultdict(list)
        for r in e6:
            try:
                by_load[r["load_level"]].append(int(r["current_replicas"]))
            except Exception:
                pass
        p(f"  N snapshots   : {len(e6)}")
        for lvl in ["idle","low","moderate","high","peak"]:
            if lvl in by_load:
                v = by_load[lvl]
                p(f"  {lvl:12s}: replicas mean={round(statistics.mean(v),1)} "
                  f"min={min(v)} max={max(v)} n={len(v)}")

        # ── PAPER TABLE SUMMARY ───────────────────────────────────────
        p()
        p("="*65)
        p("  PAPER-READY TABLE VALUES (copy into paper)")
        p("="*65)
        p()
        p("TABLE I — DEPLOYMENT PERFORMANCE COMPARISON")
        if prop_ok and base_all:
            p(f"  Proposed op. mean ± SD : {round(statistics.mean(prop_ok),3)} ± "
              f"{round(statistics.stdev(prop_ok),3)} min")
            p(f"  Baseline op. mean ± SD : {round(statistics.mean(base_all),3)} ± "
              f"{round(statistics.stdev(base_all),3)} min")
            p(f"  Reduction              : {pct}%")
            p(f"  Proposed 95% CI        : {ci95(prop_ok)}")
            p(f"  Baseline 95% CI        : {ci95(base_all)}")
            p(f"  Proposed failure rate  : {failures1}/{len(e1)}")
            p(f"  Baseline failure rate  : {failures2}/{len(e2)} ({100*failures2/max(len(e2),1):.0f}%)")
            p(f"  Welch t({df}) = {t}, p = {pv}, d = {d}")
            p(f"  Mann-Whitney U = {U}, p = {pU}")
        p()
        p("TABLE IV — ROLLBACK AND DRIFT")
        if prop_rb and base_rb:
            p(f"  Proposed rollback : {pm} ± {ps} min  [{pmn}-{pmx}]")
            p(f"  Baseline rollback : {bm} ± {bs} min  [{bmn}-{bmx}]")
            p(f"  Welch t({df}) = {t}, p = {pv}, d = {d}")
        if det:
            p(f"  Drift detection   : {dm} ± {ds} s")
            p(f"  Drift correction  : {cm} ± {cs} s")
            p(f"  Total resolution  : {tm} ± {ts2} s")

        p()
        p(f"  Statistics saved to: {out_txt}")
        p()
        p("="*65)
        p("  STAGE 5 COMPLETE")
        p("  Give Claude these files:")
        p("    outputs/exp1_proposed_deployments.csv")
        p("    outputs/exp2_baseline_deployments.csv")
        p("    outputs/exp3_drift_correction.csv")
        p("    outputs/exp4_rollback.csv")
        p("    outputs/exp5_chaos_resilience.csv")
        p("    outputs/exp6_hpa_scaling.csv")
        p("    outputs/paper_statistics.txt")
        p("    outputs/stage4_run.log")
        p("="*65)

if __name__ == "__main__":
    main()
