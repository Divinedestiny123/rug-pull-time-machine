import os
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid

load_dotenv()

# These must match the exact keys you put in Vercel!
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ ERROR: Supabase credentials missing in environment variables.")
else:
    supabase: Client = create_client(url, key)

def log_alert_to_db(tx_hash: str, dev_wallet: str, risk_score: int, flags: list):
    """
    Pushes a detected threat to the database. 
    Because your Vercel frontend uses Supabase Real-Time, 
    this will instantly pop up on your live website!
    """
    try:
        data, count = supabase.table('alerts').insert({
            "id": str(uuid.uuid4()),
            "tx_hash": tx_hash,
            "dev_wallet": dev_wallet,
            "risk_score": risk_score,
            "threat_details": flags
        }).execute()
        print(f"✅ [DATABASE] Alert successfully pushed to Vercel Dashboard!")
    except Exception as e:
        print(f"⚠️ [DATABASE] Failed to push alert: {e}")