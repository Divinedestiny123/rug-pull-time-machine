from database import log_alert_to_db

print("📡 Initiating test transmission to Supabase...")

# We are creating a fake transaction and a fake threat to test the pipes
dummy_tx_hash = "0x0000000000000000000000000000000000000000000000000000000000000000"
dummy_dev_wallet = "0x9999999999999999999999999999999999999999"
dummy_risk_score = 99
dummy_flags = [
    {
        "type": "SYSTEM_TEST", 
        "severity": 99, 
        "description": "If you are reading this, the database connection is flawless."
    }
]

# Fire the laser
log_alert_to_db(dummy_tx_hash, dummy_dev_wallet, dummy_risk_score, dummy_flags)