from database import log_alert_to_db

def analyze_transaction(tx, dev_wallet):
    red_flags = []
    
    # 1. THE DEV DUMP FLAG
    if tx.get('from', '').lower() == dev_wallet.lower():
        red_flags.append({
            "type": "DEV_WALLET_MOVEMENT",
            "severity": 40,
            "description": "Developer wallet initiated a transaction."
        })

    # 2. THE LIQUIDITY PULL FLAG
    raw_input = tx.get('input', '0x')
    input_data = "0x" + raw_input.hex() if hasattr(raw_input, 'hex') else str(raw_input)

    if input_data.startswith('0xbaa2abde') or input_data.startswith('0x02751cec'):
        red_flags.append({
            "type": "LIQUIDITY_REMOVED",
            "severity": 80,
            "description": "Liquidity removal function detected."
        })

    return red_flags

def evaluate_threat_level(tx, dev_wallet):
    flags = analyze_transaction(tx, dev_wallet)
    risk_score = min(sum(flag['severity'] for flag in flags), 100)

    if risk_score > 0:
        print(f"\n🚨 THREAT DETECTED! Risk Score: {risk_score}%")
        for flag in flags:
            print(f"   - [FLAG] {flag['type']}: {flag['description']}")
        
        # If risk is 40 or higher, push it to the live website
        if risk_score >= 40:
            print("   ⚠️ HIGH RISK: Pushing Dashboard Alert to Supabase...")
            # Safely handle the tx hash whether it's HexBytes or a string
            tx_hash_str = tx['hash'].hex() if hasattr(tx['hash'], 'hex') else str(tx['hash'])
            log_alert_to_db(tx_hash_str, dev_wallet, risk_score, flags)

    return risk_score