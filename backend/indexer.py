import os
import time
from web3 import Web3
from dotenv import load_dotenv

# NEW: Import the brain we just built!
from heuristics import evaluate_threat_level

load_dotenv()

# We pull the live RPC URL from your .env file
RPC_URL = os.getenv("MANTLE_RPC_URL")
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# --- THE VAULT & WATCHTOWER CREDENTIALS ---
# Your newly deployed contract on the live Mantle Sepolia network
VAULT_ADDRESS = "0x19470B76BD2B01Fd7F6C54a29CCD07161CDaE310"
# Securely pulling your MetaMask key from the .env file
AI_PRIVATE_KEY = os.getenv("PRIVATE_KEY") 
AI_PUBLIC_ADDRESS = "0x77b328Df6b0649c0cDA166e5DdDdE7caC029d44d"

# --- THE TARGETS ---
# In a full app, these would be dynamically pulled from your Supabase database 
# based on what tokens your users have deposited into the Vault.
# For now, we will use placeholder addresses to represent a sketchy dev and their token.
TARGET_DEV_WALLET = "0x1234567890123456789012345678901234567890" 
TARGET_TOKEN_CONTRACT = "0x0987654321098765432109876543210987654321"

def start_watchtower():
    if not web3.is_connected():
        print("❌ CRITICAL: Failed to connect to the Mantle Network.")
        return

    print(f"✅ Connected to Mantle Network! Node: {web3.client_version}")
    print(f"🛡️  Guarding Vault at: {VAULT_ADDRESS}")
    print(f"🎯 Locking radar on Dev Wallet: {TARGET_DEV_WALLET}")
    print("👁️  Watchtower is online. Scanning for new blocks...\n")

    latest_known_block = web3.eth.block_number - 5
    
    print(f"Rewinding 5 blocks to {latest_known_block} to ensure nothing was missed...")

    while True:
        try:
            current_block = web3.eth.block_number
            
            if current_block > latest_known_block:
                print(f"🧱 [BLOCK {current_block}] Intercepted and scanning...")
                
                block_data = web3.eth.get_block(current_block, full_transactions=True)
                
                # --- THE ANALYSIS LOOP ---
                # We crack open the block and look at every transaction inside
                for tx in block_data.transactions:
                    
                    # web3.py returns dictionary-like objects, we need the sender ('from') and receiver ('to')
                    tx_sender = tx.get('from', '').lower()
                    tx_receiver = tx.get('to', '')
                    if tx_receiver:
                        tx_receiver = tx_receiver.lower()
                    
                    # OPTIMIZATION: Only run the heavy AI math if the transaction involves our target dev or token
                    if tx_sender == TARGET_DEV_WALLET.lower() or tx_receiver == TARGET_TOKEN_CONTRACT.lower():
                        print(f"   🔍 Target activity detected! TxHash: {tx['hash'].hex()}")
                        
                        # Feed the raw transaction data into the heuristics brain
                        evaluate_threat_level(tx, TARGET_DEV_WALLET, TARGET_TOKEN_CONTRACT)

                latest_known_block = current_block
            
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ Network glitch or error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_watchtower()