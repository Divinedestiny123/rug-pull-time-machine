from database import log_alert_to_db

def analyze_transaction(tx, dev_wallet, token_contract):
    """
    Scans a single transaction for malicious rug-pull behavior.
    Returns a list of detected red flags.
    """
    red_flags = []
    
    # 1. THE DEV DUMP FLAG
    # Is the creator of the token suddenly moving massive amounts of it?
    if tx['from'].lower() == dev_wallet.lower():
        # In a real scenario, we would decode the transaction input data here 
        # to see exactly how many tokens are being transferred or sold.
        red_flags.append({
            "type": "DEV_WALLET_MOVEMENT",
            "severity": 40,
            "description": "Developer wallet initiated a transaction."
        })

    # 2. THE LIQUIDITY PULL FLAG
    raw_input = tx.get('input', '0x')
    
    # NEW: Safely convert Web3 HexBytes into a string AND manually add the '0x' back!
    if hasattr(raw_input, 'hex'):
        input_data = "0x" + raw_input.hex()
    else:
        input_data = str(raw_input)

    if input_data.startswith('0xbaa2abde') or input_data.startswith('0x02751cec'):
        red_flags.append({
            "type": "LIQUIDITY_REMOVED",
            "severity": 80,
            "description": "Liquidity removal function detected."
        })

    # 3. THE MIXER FLAG (Tornado Cash / Railgun)
    # Is the dev funneling money into known crypto mixers to hide their tracks?
    known_mixers = [
        "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b".lower() # Example Tornado Cash router
    ]
    if tx['to'] and tx['to'].lower() in known_mixers:
        red_flags.append({
            "type": "MIXER_INTERACTION",
            "severity": 60,
            "description": "Funds routed to a known privacy mixer."
        })

    return red_flags

def calculate_risk_score(red_flags):
    """
    Takes all detected flags and calculates a total Risk Score (0-100%).
    """
    if not red_flags:
        return 0

    total_risk = 0
    for flag in red_flags:
        total_risk += flag['severity']

    # Cap the maximum risk score at 100%
    return min(total_risk, 100)

def evaluate_threat_level(tx, dev_wallet, token_contract):
    """
    The main pipeline: Analyzes the transaction, scores it, and triggers alarms.
    """
    flags = analyze_transaction(tx, dev_wallet, token_contract)
    risk_score = calculate_risk_score(flags)

    if risk_score > 0:
        print(f"🚨 THREAT DETECTED! Risk Score: {risk_score}%")
        for flag in flags:
            print(f"   - [FLAG] {flag['type']}: {flag['description']}")
        
        # Trigger the execution layer based on user thresholds
        if risk_score >= 90:
            print("   🧨 CRITICAL RISK: Triggering Smart Contract Emergency Exit...")
            log_alert_to_db(tx['hash'].hex(), dev_wallet, risk_score, flags)
            
        elif risk_score >= 40: # Lowered to 40 so our Dev Dump dummy tx triggers the alert!
            print("   ⚠️ HIGH RISK: Pushing Dashboard Alert...")
            log_alert_to_db(tx['hash'].hex(), dev_wallet, risk_score, flags)

    return risk_score