"""
seed.py — populate instech-ai with realistic Indian sample data.
Run once against the live API:
    python seed.py
"""
import requests
import random
from datetime import date, timedelta

API = "http://localhost:8000"

LOCATIONS = [
    {"address": "Connaught Place, New Delhi",           "lat": 28.6315, "lon": 77.2167},
    {"address": "Karol Bagh, New Delhi",                "lat": 28.6519, "lon": 77.1907},
    {"address": "Bandra West, Mumbai",                  "lat": 19.0596, "lon": 72.8295},
    {"address": "Andheri East, Mumbai",                 "lat": 19.1136, "lon": 72.8697},
    {"address": "Koramangala, Bengaluru",               "lat": 12.9352, "lon": 77.6245},
    {"address": "Whitefield, Bengaluru",                "lat": 12.9698, "lon": 77.7500},
    {"address": "T. Nagar, Chennai",                    "lat": 13.0418, "lon": 80.2341},
    {"address": "Adyar, Chennai",                       "lat": 13.0012, "lon": 80.2565},
    {"address": "Salt Lake City, Kolkata",              "lat": 22.5744, "lon": 88.4146},
    {"address": "Park Street, Kolkata",                 "lat": 22.5513, "lon": 88.3512},
    {"address": "Banjara Hills, Hyderabad",             "lat": 17.4156, "lon": 78.4347},
    {"address": "HITEC City, Hyderabad",                "lat": 17.4474, "lon": 78.3762},
    {"address": "Aundh, Pune",                          "lat": 18.5590, "lon": 73.8080},
    {"address": "Kothrud, Pune",                        "lat": 18.5074, "lon": 73.8077},
    {"address": "Navrangpura, Ahmedabad",               "lat": 23.0395, "lon": 72.5614},
    {"address": "Satellite, Ahmedabad",                 "lat": 23.0226, "lon": 72.5108},
    {"address": "Civil Lines, Jaipur",                  "lat": 26.9259, "lon": 75.7873},
    {"address": "Vaishali Nagar, Jaipur",               "lat": 26.9115, "lon": 75.7311},
    {"address": "Gomti Nagar, Lucknow",                 "lat": 26.8581, "lon": 81.0005},
    {"address": "Hazratganj, Lucknow",                  "lat": 26.8508, "lon": 80.9491},
    {"address": "Powai, Mumbai",                        "lat": 19.1176, "lon": 72.9060},
    {"address": "Electronic City, Bengaluru",           "lat": 12.8399, "lon": 77.6770},
    {"address": "Mylapore, Chennai",                    "lat": 13.0368, "lon": 80.2676},
    {"address": "Alipore, Kolkata",                     "lat": 22.5269, "lon": 88.3377},
    {"address": "Jubilee Hills, Hyderabad",             "lat": 17.4239, "lon": 78.4139},
    {"address": "Viman Nagar, Pune",                    "lat": 18.5679, "lon": 73.9143},
    {"address": "Sector 18, Noida",                     "lat": 28.5706, "lon": 77.3219},
    {"address": "DLF Phase 2, Gurugram",                "lat": 28.4804, "lon": 77.0878},
    {"address": "Marine Drive, Mumbai",                 "lat": 18.9440, "lon": 72.8237},
    {"address": "New Palasia, Indore",                  "lat": 22.7246, "lon": 75.8816},
    {"address": "Vijay Nagar, Indore",                  "lat": 22.7533, "lon": 75.8937},
    {"address": "Gandhinagar, Gujarat",                 "lat": 23.2156, "lon": 72.6369},
    {"address": "Vastrapur, Ahmedabad",                 "lat": 23.0376, "lon": 72.5301},
    {"address": "Navi Mumbai, Maharashtra",             "lat": 19.0330, "lon": 73.0297},
    {"address": "Malviya Nagar, New Delhi",             "lat": 28.5271, "lon": 77.2032},
    {"address": "Anna Nagar, Chennai",                  "lat": 13.0850, "lon": 80.2101},
    {"address": "Yelahanka, Bengaluru",                 "lat": 13.1005, "lon": 77.5963},
    {"address": "Kompally, Hyderabad",                  "lat": 17.5411, "lon": 78.4867},
    {"address": "Hinjawadi, Pune",                      "lat": 18.5912, "lon": 73.7381},
    {"address": "Boring Road, Patna",                   "lat": 25.6126, "lon": 85.1251},
]

CUSTOMERS = [
    {"name": "Arjun Sharma",       "email": "arjun.sharma@example.in",    "phone": "+91-98100-11234"},
    {"name": "Priya Patel",        "email": "priya.patel@example.in",     "phone": "+91-98200-22345"},
    {"name": "Rahul Verma",        "email": "rahul.verma@example.in",     "phone": "+91-98300-33456"},
    {"name": "Sneha Iyer",         "email": "sneha.iyer@example.in",      "phone": "+91-98400-44567"},
    {"name": "Vikram Singh",       "email": "vikram.singh@example.in",    "phone": "+91-98500-55678"},
    {"name": "Ananya Chatterjee",  "email": "ananya.c@example.in",        "phone": "+91-98600-66789"},
    {"name": "Rohan Mehta",        "email": "rohan.mehta@example.in",     "phone": "+91-98700-77890"},
    {"name": "Divya Nair",         "email": "divya.nair@example.in",      "phone": "+91-98800-88901"},
    {"name": "Aditya Kumar",       "email": "aditya.kumar@example.in",    "phone": "+91-98900-99012"},
    {"name": "Kavya Reddy",        "email": "kavya.reddy@example.in",     "phone": "+91-97000-10123"},
    {"name": "Sanjay Gupta",       "email": "sanjay.gupta@example.in",    "phone": "+91-97100-21234"},
    {"name": "Meera Joshi",        "email": "meera.joshi@example.in",     "phone": "+91-97200-32345"},
    {"name": "Kunal Bose",         "email": "kunal.bose@example.in",      "phone": "+91-97300-43456"},
    {"name": "Pooja Agarwal",      "email": "pooja.agarwal@example.in",   "phone": "+91-97400-54567"},
    {"name": "Nikhil Tiwari",      "email": "nikhil.tiwari@example.in",   "phone": "+91-97500-65678"},
]

POLICY_TYPES = ["home", "flood", "fire", "auto"]
CLAIM_TYPES  = ["flood", "fire", "theft", "accident", "other"]

# Realistic Indian sum insured (INR) per IRDAI norms
SUM_INSURED_BY_TYPE = {
    "home":  [2_000_000, 3_500_000, 5_000_000, 7_500_000, 10_000_000],
    "flood": [1_500_000, 2_500_000, 4_000_000, 6_000_000,  7_500_000],
    "fire":  [1_000_000, 2_000_000, 3_500_000, 5_000_000,  7_000_000],
    "auto":  [  300_000,   500_000,   750_000, 1_000_000,  1_500_000],
}

# Annual premium rate range per type (IRDAI-aligned)
PREMIUM_RATE_BY_TYPE = {
    "home":  (0.005, 0.012),
    "flood": (0.008, 0.018),
    "fire":  (0.006, 0.015),
    "auto":  (0.020, 0.040),
}

CLAIM_AMOUNTS_BY_TYPE = {
    "flood":    [50_000, 120_000, 250_000,   400_000,   800_000, 1_500_000],
    "fire":     [80_000, 200_000, 350_000,   600_000, 1_000_000],
    "theft":    [30_000,  80_000, 150_000,   300_000,   500_000],
    "accident": [25_000,  60_000, 120_000,   200_000,   400_000],
    "other":    [20_000,  50_000, 100_000,   180_000,   300_000],
}


def post(path, payload):
    r = requests.post(f"{API}{path}", json=payload, timeout=15)
    if r.status_code in (200, 201):
        return r.json()
    print(f"  ✗ {path} → {r.status_code}: {r.text[:150]}")
    return None


def run():
    print("── instech-ai seed (India) ──────────────────────────")

    # 1. Customers
    print(f"\n[1/4] Creating {len(CUSTOMERS)} customers...")
    customer_ids = []
    for c in CUSTOMERS:
        result = post("/customers/", c)
        if result:
            customer_ids.append(result["id"])
            print(f"  ✓ #{result['id']:3d} — {c['name']}")

    if not customer_ids:
        print("\n✗ No customers created. Is docker running?")
        print("  Check: http://localhost:8000/docs")
        return

    # 2. Policies — 2 per customer
    print(f"\n[2/4] Creating policies with auto risk scoring...")
    policy_ids   = []
    policy_types = {}
    loc_pool     = LOCATIONS.copy()
    random.shuffle(loc_pool)

    for i, cid in enumerate(customer_ids):
        for j in range(2):
            loc   = loc_pool[(i * 2 + j) % len(loc_pool)]
            ptype = POLICY_TYPES[(i + j) % len(POLICY_TYPES)]
            si    = random.choice(SUM_INSURED_BY_TYPE[ptype])
            lo, hi = PREMIUM_RATE_BY_TYPE[ptype]
            prem  = int(si * random.uniform(lo, hi))
            start = date.today() - timedelta(days=random.randint(15, 400))
            end   = start + timedelta(days=365)

            result = post("/policies/", {
                "customer_id": cid,
                "address":     loc["address"],
                "lat":         loc["lat"],
                "lon":         loc["lon"],
                "policy_type": ptype,
                "sum_insured": si,
                "premium":     prem,
                "start_date":  str(start),
                "end_date":    str(end),
            })
            if result:
                pid   = result["id"]
                score = result.get("risk_score", "—")
                policy_ids.append(pid)
                policy_types[pid] = ptype
                print(
                    f"  ✓ #{pid:3d} {ptype:5s} | {loc['address'][:38]:38s}"
                    f" | SI: ₹{si:>11,.0f} | prem: ₹{prem:>7,.0f} | risk: {score}"
                )

    # 3. Claims
    print(f"\n[3/4] Filing claims...")
    claim_ids = []
    for pid in policy_ids:
        n_claims = random.choices([0, 1, 2, 3], weights=[20, 45, 25, 10])[0]
        for _ in range(n_claims):
            ctype  = random.choice(CLAIM_TYPES)
            amount = random.choice(CLAIM_AMOUNTS_BY_TYPE.get(ctype, [100_000]))
            result = post("/claims/", {
                "policy_id":        pid,
                "claim_type":       ctype,
                "amount_requested": amount,
                "description":      f"{ctype.capitalize()} damage at insured property.",
            })
            if result:
                claim_ids.append(result["id"])
                print(f"  ✓ claim #{result['id']:3d} — {ctype:8s} ₹{amount:>10,.0f}  on policy #{pid}")

    # 4. Fraud detection
    print(f"\n[4/4] Running fraud detection on {len(claim_ids)} claims...")
    flagged = reviewed = clear = 0
    for cid in claim_ids:
        result = post(f"/claims/{cid}/fraud-check", {})
        if result:
            decision = result.get("decision", "—")
            prob     = result.get("fraud_probability", 0)
            flags    = result.get("risk_flags", [])
            if decision == "flag":
                marker = "🚩"; flagged += 1
            elif decision == "review":
                marker = "⚠ "; reviewed += 1
            else:
                marker = "✓ "; clear += 1
            flag_str = ", ".join(flags) if flags else "none"
            print(f"  {marker} claim #{cid:3d} — {decision:6s} prob:{prob:.2f}  [{flag_str}]")

    print(f"""
── done ─────────────────────────────────────────────
   {len(customer_ids):3d}  customers
   {len(policy_ids):3d}  policies  (risk scored via Open-Meteo + XGBoost)
   {len(claim_ids):3d}  claims    (fraud checked)
        ✓  clear:   {clear}
        ⚠  review:  {reviewed}
        🚩  flagged: {flagged}

   Dashboard → http://localhost:8501
   Swagger   → http://localhost:8000/docs
""")


if __name__ == "__main__":
    random.seed(42)
    run()
