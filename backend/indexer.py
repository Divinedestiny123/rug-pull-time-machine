import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from web3 import Web3

# 1. THE HEALTH SERVER (REQUIRED FOR RENDER FREE TIER)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ALIVE")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"📡 Render Health Check started on port {port}")
    server.serve_forever()

# 2. THE ACTUAL AI WATCHTOWER LOGIC
def start_watchtower():
    print("🚀 Godseye Watchtower AI Initializing...")
    
    # Connect to Mantle
    rpc_url = os.environ.get("MANTLE_RPC_URL")
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not web3.is_connected():
        print("❌ FAILED to connect to Mantle. Check your RPC_URL variable!")
        return

    print(f"✅ Connected to Mantle. Monitoring from block {web3.eth.block_number}")
    latest_block = web3.eth.block_number - 1

    while True:
        try:
            current_block = web3.eth.block_number
            if current_block > latest_block:
                # THIS IS THE LOG WE ARE LOOKING FOR
                print(f"🧱 [BLOCK {current_block}] Intercepted and scanning...")
                
                # --- YOUR HEURISTICS LOGIC GOES HERE ---
                # (The part where you loop through transactions)
                
                latest_block = current_block
            
            time.sleep(2) # Mantle blocks are fast!
        except Exception as e:
            print(f"⚠️ Loop Error: {e}")
            time.sleep(5)

# 3. THE "LAUNCHPAD"
if __name__ == "__main__":
    # Start Health Server in a separate thread
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # Run the Watchtower in the main thread
    start_watchtower()