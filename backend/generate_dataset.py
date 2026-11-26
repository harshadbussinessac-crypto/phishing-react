"""Generate a larger, varied training set of phishing and safe emails.

Usage (from backend/):  python generate_dataset.py
Writes data/emails_generated.csv with columns: text,label (1 = phishing, 0 = safe)

NOTE: these are template-generated emails. They cover many brands, wordings,
and link styles, and include hard "safe" examples that use urgent words and
links. Real-world accuracy still needs a public corpus (e.g. SpamAssassin,
Nazario) for evaluation.
"""
import csv
import random
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parent / "data" / "emails_generated.csv"
N_PER_CLASS = 400

BRANDS = ["PayPal", "Microsoft 365", "Apple ID", "Netflix", "Chase Bank", "DHL",
          "Amazon", "Dropbox", "Google Workspace", "your university portal", "HMRC", "DocuSign"]
BAD_TLDS = [".xyz", ".top", ".club", ".online", ".info", ".tk", ".ml", ".site", ".buzz"]
BAD_WORDS = ["secure", "verify", "login", "account", "update", "billing", "support"]
GOOD_HOSTS = ["docs.company.com", "www.example.org", "intranet.university.edu",
              "github.com", "www.ups.com", "calendar.google.com", "www.irs.gov"]
GREETINGS = ["Dear customer", "Hi there", "Hello", "Dear user", "Dear account holder", "Hi"]
PHISH_PRESSURE = [
    "Your account will be suspended within 24 hours.",
    "Unusual sign-in activity was detected.",
    "We could not verify your identity.",
    "Immediate action is required to avoid losing access.",
    "Your payment details have expired.",
    "A new device attempted to access your account.",
    "Your mailbox storage is full and mail will be blocked.",
]
PHISH_ASKS = [
    "Please verify your password and card details.",
    "Re-enter your login credentials to confirm ownership.",
    "Confirm your bank details to release the pending funds.",
    "Upload your ID to restore full access.",
    "Click the button below and sign in to keep your account active.",
]
SAFE_BODIES = [
    "Attached are the notes from Tuesday's meeting. Let me know if I missed anything.",
    "Your order has shipped and should arrive on Thursday.",
    "Thanks for joining the webinar. The recording is available on the team site.",
    "Reminder: the project review is moved to Friday at 2pm.",
    "Please find the invoice for last month attached. Payment is due in 30 days.",
    "Your appointment is confirmed. Reply if you need to reschedule.",
    "Here is the updated schedule for next week's workshop.",
    "Your password was changed successfully. If this was not you, contact IT support.",
    "The quarterly report is ready for review in the shared folder.",
    "Welcome aboard! Here are a few tips to get started with the new tool.",
]
SAFE_SIGNOFFS = ["Best regards", "Thanks", "Cheers", "Kind regards", "Sincerely"]
SENDERS = ["Anna", "Mark", "Priya", "Jordan", "the Accounts team", "Support Desk", "Dan"]


def rand_bad_url():
    host = f"{random.choice(BAD_WORDS)}-{random.choice(BRANDS).split()[0].lower()}{random.choice(BAD_TLDS)}"
    path = random.choice(["/login", "/verify", "/update", "/confirm?id=" + str(random.randint(1000, 9999))])
    scheme = random.choice(["http://", "http://", "https://"])
    if random.random() < 0.15:
        host = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    if random.random() < 0.1:
        return f"{scheme}bit.ly/{random.randint(100, 999)}x"
    return f"{scheme}{host}{path}"


def rand_good_url():
    host = random.choice(GOOD_HOSTS)
    return f"https://{host}/{random.choice(['agenda', 'docs', 'invoices', 'schedule', 'help'])}"


def phishing_email():
    brand = random.choice(BRANDS)
    parts = [
        f"{random.choice(GREETINGS)}, this is an alert from {brand}.",
        random.choice(PHISH_PRESSURE),
        random.choice(PHISH_ASKS),
    ]
    for _ in range(random.randint(0, 2)):
        parts.append(f"Visit {rand_bad_url()} now.")
    if random.random() < 0.4:
        parts.append(random.choice(["ACT NOW!!!", "URGENT!", "Final warning!"]))
    if random.random() < 0.3:
        random.shuffle(parts)
    return " ".join(parts)


def safe_email():
    parts = [f"{random.choice(GREETINGS)},", random.choice(SAFE_BODIES)]
    if random.random() < 0.5:
        parts.append(f"Link: {rand_good_url()}")
    # hard negatives: legitimate mail that uses urgent-sounding words or account talk
    if random.random() < 0.25:
        parts.append(random.choice([
            "Please update the document before the deadline, it is urgent for the client.",
            "Your password expires in 90 days, so you can change it in the settings page.",
            "Verify the figures in the attached sheet when you have a moment.",
            "This is a reminder to confirm your attendance by Friday.",
        ]))
    parts.append(f"{random.choice(SAFE_SIGNOFFS)}, {random.choice(SENDERS)}.")
    return " ".join(parts)


def main():
    rows, seen = [], set()
    while sum(r[1] for r in rows) < N_PER_CLASS or sum(1 - r[1] for r in rows) < N_PER_CLASS:
        if sum(r[1] for r in rows) < N_PER_CLASS:
            t = phishing_email()
            if t not in seen:
                seen.add(t)
                rows.append((t, 1))
        if sum(1 - r[1] for r in rows) < N_PER_CLASS:
            t = safe_email()
            if t not in seen:
                seen.add(t)
                rows.append((t, 0))
    random.shuffle(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "label"])
        w.writerows(rows)
    print(f"Wrote {len(rows)} emails to {OUT} ({N_PER_CLASS} per class)")


if __name__ == "__main__":
    main()
