import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load the keys from .env
load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

# Initialize the Supabase connection
supabase: Client = create_client(url, key)

def log_alert_to_db(tx_hash, dev_wallet, risk_score, flags):
    """
    Pushes a detected threat to the Supabase database.
    """
    try:
        data = {
            "tx_hash": tx_hash,
            "dev_wallet": dev_wallet,
            "risk_score": risk_score,
            "threat_details": flags # We save the exact red flags as JSON
        }
        
        # Insert the data into the 'alerts' table we just made
        response = supabase.table("alerts").insert(data).execute()
        print(f"✅ Threat securely logged to Supabase! ID: {response.data[0]['id']}")
        
    except Exception as e:
        print(f"❌ Failed to log threat to database: {e}")