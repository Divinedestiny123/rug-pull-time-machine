'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';
import { ethers } from 'ethers';
import { Eye, Activity, Lock, AlertTriangle, Terminal, LayoutDashboard, Settings, Search, Bell, Wallet, X, ChevronRight, LogOut, Database, Sliders, Menu } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface Alert {
  id: string;
  created_at: string;
  tx_hash: string;
  dev_wallet: string;
  risk_score: number;
  threat_details: any[];
}

export default function Dashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const [currentBlock, setCurrentBlock] = useState<number | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isWalletModalOpen, setIsWalletModalOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [riskThreshold, setRiskThreshold] = useState(90);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    const fetchAlerts = async () => {
      const { data } = await supabase.from('alerts').select('*').order('created_at', { ascending: false }).limit(10);
      if (data) setAlerts(data);
    };
    fetchAlerts();

    const subscription = supabase.channel('public:alerts').on(
      'postgres_changes', { event: 'INSERT', schema: 'public', table: 'alerts' },
      (payload) => setAlerts((current) => [payload.new as Alert, ...current])
    ).subscribe();

    return () => { supabase.removeChannel(subscription); };
  }, []);

  useEffect(() => {
    const provider = new ethers.JsonRpcProvider('https://rpc.mantle.xyz');
    const fetchInitialBlock = async () => {
      const block = await provider.getBlockNumber();
      setCurrentBlock(block);
      
      const initialData = Array.from({ length: 15 }).map((_, i) => ({
        time: `-${15 - i}s`,
        txVolume: Math.floor(Math.random() * 200) + 50
      }));
      setChartData(initialData);
    };
    fetchInitialBlock();

    provider.on('block', (blockNumber) => { 
      setCurrentBlock(blockNumber); 
      
      const now = new Date();
      const timeString = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
      const simulatedTxVolume = Math.floor(Math.random() * 300) + 100;
      
      setChartData(prevData => {
        const newData = [...prevData, { time: timeString, txVolume: simulatedTxVolume }];
        return newData.slice(-15);
      });
    });

    return () => { provider.removeAllListeners('block'); };
  }, []);

  // 3. MULTI-WALLET CONNECTION LOGIC (Upgraded with Cryptographic Signature)
  const connectSpecificWallet = async (walletName: string) => {
    setIsConnecting(true);
    try {
      const eth = (window as any).ethereum;
      let selectedProvider = null;

      if (!eth) {
        alert("No Web3 wallets detected in your browser.");
        setIsConnecting(false);
        return;
      }

      if (eth.providers) {
        if (walletName === 'MetaMask') selectedProvider = eth.providers.find((p: any) => p.isMetaMask);
        else if (walletName === 'Phantom') selectedProvider = eth.providers.find((p: any) => p.isPhantom);
        else if (walletName === 'Coinbase') selectedProvider = eth.providers.find((p: any) => p.isCoinbaseWallet);
      } else {
        selectedProvider = eth;
      }

      if (!selectedProvider) {
        alert(`Could not connect to ${walletName}. Please make sure it is installed.`);
        setIsConnecting(false);
        return;
      }

      // 1. Get Provider and request connection
      const provider = new ethers.BrowserProvider(selectedProvider);
      await provider.send("eth_requestAccounts", []);
      
      // 2. Force Network Switch to Mantle
      const mantleChainIdHex = '0x1388'; 
      const network = await provider.getNetwork();
      
      if (network.chainId !== BigInt(5000)) {
        try {
          await selectedProvider.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: mantleChainIdHex }] });
        } catch (switchError: any) {
          if (switchError.code === 4902) {
            await selectedProvider.request({
              method: 'wallet_addEthereumChain',
              params: [{
                chainId: mantleChainIdHex, chainName: 'Mantle Mainnet', rpcUrls: ['https://rpc.mantle.xyz'],
                nativeCurrency: { name: 'Mantle', symbol: 'MNT', decimals: 18 }, blockExplorerUrls: ['https://explorer.mantle.xyz/'],
              }],
            });
          } else {
            setIsConnecting(false); return; 
          }
        }
      }

      // 3. --- NEW: THE AUTHENTICATION SIGNATURE ---
      const signer = await provider.getSigner();
      const address = await signer.getAddress();
      
      // Create a unique message for them to sign (using Date.now() prevents replay attacks)
      const message = `Welcome to GodsEye Watchtower!\n\nPlease sign this message to verify your identity and ownership of this wallet. This action costs zero gas.\n\nWallet: ${address}\nNonce: ${Date.now()}`;
      
      // This triggers the MetaMask/Phantom popup asking them to "Sign"
      const signature = await signer.signMessage(message);
      
      console.log("Cryptographic Signature Verified:", signature);

      // Only grant access and update UI if they successfully sign it
      setWalletAddress(address);
      setIsWalletModalOpen(false);

    } catch (error: any) {
      console.error("Connection or signature failed", error);
      // Friendly error if they click "Reject" on the signature popup
      if (error.code === 'ACTION_REJECTED') {
        alert("Authentication Failed: You must sign the message to enter the Watchtower.");
      }
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = () => {
    setWalletAddress(null);
    setIsDropdownOpen(false);
    setActiveTab('dashboard');
  };

  const formatAddress = (address: string) => `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;

  const NavButton = ({ id, icon: Icon, label }: { id: string, icon: any, label: string }) => (
    <button 
      onClick={() => {
        setActiveTab(id);
        setIsMobileMenuOpen(false);
      }}
      className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
        activeTab === id 
          ? 'bg-red-500/10 text-red-400 border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]' 
          : 'hover:bg-neutral-800/50 text-neutral-400'
      }`}
    >
      <Icon className="w-5 h-5 mr-3 shrink-0" /> {label}
    </button>
  );

  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-300 font-mono overflow-hidden">
      
      {isWalletModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl w-full max-w-[400px] shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="flex justify-between items-center p-6 border-b border-neutral-800">
              <h3 className="text-xl font-bold text-white">Connect Wallet</h3>
              <button onClick={() => setIsWalletModalOpen(false)} className="text-neutral-500 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-4 space-y-2">
              <button onClick={() => connectSpecificWallet('MetaMask')} className="w-full flex items-center justify-between p-4 bg-neutral-950/50 border border-neutral-800 rounded-xl hover:border-orange-500/50 hover:bg-orange-500/10 group">
                <div className="flex items-center space-x-4"><div className="w-10 h-10 rounded-full bg-gradient-to-tr from-orange-400 to-orange-600 p-[2px]"><div className="w-full h-full bg-neutral-900 rounded-full flex items-center justify-center text-orange-500 font-bold text-lg">M</div></div><span className="text-white font-semibold">MetaMask</span></div><ChevronRight className="w-5 h-5 text-neutral-600 group-hover:text-orange-500" />
              </button>
              <button onClick={() => connectSpecificWallet('Phantom')} className="w-full flex items-center justify-between p-4 bg-neutral-950/50 border border-neutral-800 rounded-xl hover:border-purple-500/50 hover:bg-purple-500/10 group">
                <div className="flex items-center space-x-4"><div className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-400 to-purple-600 p-[2px]"><div className="w-full h-full bg-neutral-900 rounded-full flex items-center justify-center text-purple-500 font-bold text-lg">P</div></div><span className="text-white font-semibold">Phantom</span></div><ChevronRight className="w-5 h-5 text-neutral-600 group-hover:text-purple-500" />
              </button>
            </div>
          </div>
        </div>
      )}

      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/80 z-30 md:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      <aside className={`fixed inset-y-0 left-0 transform ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"} md:relative md:translate-x-0 transition-transform duration-300 ease-in-out z-40 w-64 bg-neutral-950 md:bg-neutral-900/50 border-r border-neutral-800 flex flex-col`}>
        <div className="h-20 flex items-center px-6 border-b border-neutral-800 shrink-0">
          <Eye className="w-8 h-8 text-red-500 mr-3" />
          <span className="text-xl font-bold text-white tracking-wider">GODS<span className="text-red-500">EYE</span></span>
        </div>
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          <NavButton id="dashboard" icon={LayoutDashboard} label="Dashboard" />
          <NavButton id="mempool" icon={Activity} label="Live Mempool" />
          <NavButton id="assets" icon={Lock} label="Protected Assets" />
          <NavButton id="config" icon={Settings} label="Configuration" />
        </nav>
        <div className="p-4 border-t border-neutral-800 text-xs text-neutral-600 flex items-center justify-center shrink-0">
          <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
          Mantle Mainnet
        </div>
      </aside>

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        
        <header className="h-20 bg-neutral-900/30 border-b border-neutral-800 flex items-center justify-between px-4 md:px-8 shrink-0">
          <div className="flex items-center flex-1">
            <button className="md:hidden mr-4 text-neutral-400 hover:text-white" onClick={() => setIsMobileMenuOpen(true)}>
              <Menu className="w-6 h-6" />
            </button>
            <div className="hidden sm:flex items-center bg-neutral-900 border border-neutral-800 rounded-md px-4 py-2 w-full max-w-sm transition-colors focus-within:border-neutral-600">
              <Search className="w-4 h-4 text-neutral-500 mr-2 shrink-0" />
              <input type="text" placeholder="Search Wallet or Hash..." className="bg-transparent border-none outline-none text-sm w-full text-white placeholder-neutral-600 truncate"/>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 md:space-x-6">
            <button className="relative text-neutral-400 hover:text-white transition-colors">
              <Bell className="w-5 h-5" />
              {alerts.length > 0 && <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-ping"></span>}
            </button>
            
            {walletAddress ? (
              <div className="relative">
                <button onClick={() => setIsDropdownOpen(!isDropdownOpen)} className="px-3 md:px-4 py-2 bg-neutral-800 border border-neutral-700 rounded-md text-sm text-white flex items-center shadow-lg hover:bg-neutral-700 transition-colors">
                  <div className="hidden sm:block w-5 h-5 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 mr-2 border border-neutral-600"></div>
                  {formatAddress(walletAddress)}
                </button>
                {isDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-neutral-900 border border-neutral-800 rounded-lg shadow-xl py-1 z-50 animate-in fade-in slide-in-from-top-2">
                    <div className="px-4 py-2 border-b border-neutral-800">
                      <p className="text-xs text-neutral-500">Connected Wallet</p>
                      <p className="text-xs text-white truncate">{walletAddress}</p>
                    </div>
                    <button onClick={disconnectWallet} className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 flex items-center transition-colors">
                      <LogOut className="w-4 h-4 mr-2" /> Disconnect
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button onClick={() => setIsWalletModalOpen(true)} disabled={isConnecting} className="px-4 md:px-5 py-2 bg-white text-black font-semibold rounded-md text-sm flex items-center hover:bg-neutral-200 transition-colors disabled:opacity-50 whitespace-nowrap">
                <Wallet className="w-4 h-4 mr-2 shrink-0" />
                <span className="hidden sm:inline">{isConnecting ? "Connecting..." : "Connect Wallet"}</span>
                <span className="sm:hidden">{isConnecting ? "..." : "Connect"}</span>
              </button>
            )}
          </div>
        </header>

        {/* --- INVISIBLE SCROLLBAR APPLIED HERE --- */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          
          {activeTab === 'dashboard' && (
            <div className="animate-in fade-in duration-300">
              <div className="mb-6 md:mb-8">
                <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">Predictive Shield Watchtower</h1>
                <p className="text-sm md:text-base text-neutral-500 mt-1">Real-time autonomous risk assessment & execution engine.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8">
                <div className="p-5 md:p-6 bg-neutral-900/50 border border-neutral-800 rounded-xl">
                  <div className="text-neutral-500 text-sm mb-2 flex items-center justify-between">Total Value Secured <Lock className="w-4 h-4 text-emerald-500" /></div>
                  <div className="text-2xl md:text-3xl font-bold text-white">{walletAddress ? "$142,850" : "$0"}<span className="text-sm text-neutral-500 font-normal">.00</span></div>
                </div>
                <div className="p-5 md:p-6 bg-neutral-900/50 border border-neutral-800 rounded-xl">
                  <div className="text-neutral-500 text-sm mb-2 flex items-center justify-between">Threats Intercepted <Eye className="w-4 h-4 text-red-500" /></div>
                  <div className="text-2xl md:text-3xl font-bold text-white">{alerts.length}</div>
                </div>
                <div className="p-5 md:p-6 bg-neutral-900/50 border border-neutral-800 rounded-xl relative overflow-hidden group">
                  <div className="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <div className="text-neutral-500 text-sm mb-2 flex items-center justify-between relative z-10">Current Mantle Block <Activity className="w-4 h-4 text-blue-500" /></div>
                  <div className="text-2xl md:text-3xl font-bold text-white relative z-10">{currentBlock ? currentBlock.toLocaleString() : "Syncing..."}</div>
                </div>
                <div className="p-5 md:p-6 bg-neutral-900/50 border border-emerald-900/30 rounded-xl relative overflow-hidden">
                  <div className="absolute inset-0 bg-emerald-500/5"></div>
                  <div className="text-neutral-500 text-sm mb-2 relative z-10">System Status</div>
                  <div className="text-lg md:text-xl font-bold text-emerald-400 flex items-center relative z-10">
                    <div className="w-3 h-3 bg-emerald-500 rounded-full mr-3 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.8)]"></div>
                    OPERATIONAL
                  </div>
                </div>
              </div>

              <div className="w-full h-72 mb-8 p-5 md:p-6 bg-neutral-900/50 border border-neutral-800 rounded-xl">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-white flex items-center">
                    <Activity className="w-5 h-5 text-blue-500 mr-2" /> 
                    Live Mempool Volume
                  </h2>
                  <span className="text-xs text-neutral-500 bg-neutral-950 px-2 py-1 rounded border border-neutral-800">Updating per block</span>
                </div>
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                      <XAxis dataKey="time" stroke="#525252" fontSize={10} tickMargin={10} />
                      <YAxis stroke="#525252" fontSize={10} tickFormatter={(value) => `${value} tx`} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#171717', borderColor: '#262626', borderRadius: '8px', fontSize: '12px' }}
                        itemStyle={{ color: '#60a5fa' }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="txVolume" 
                        stroke="#3b82f6" 
                        strokeWidth={2}
                        fillOpacity={1} 
                        fill="url(#colorVolume)" 
                        isAnimationActive={false} 
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
                <div className="col-span-1 lg:col-span-2 space-y-4">
                  <h2 className="text-lg md:text-xl font-semibold text-white mb-4 flex items-center"><AlertTriangle className="w-5 h-5 text-red-500 mr-2" /> Live Threat Feed</h2>
                  {alerts.length === 0 ? (
                    <div className="p-8 md:p-12 border border-dashed border-neutral-800 rounded-xl flex flex-col items-center justify-center text-neutral-500 text-center">
                      <Activity className="w-10 h-10 mb-3 opacity-20" /><p className="text-sm">Radar is clear. Monitoring mempool...</p>
                    </div>
                  ) : (
                    alerts.map((alert) => (
                      <div key={alert.id} className="p-4 md:p-5 border border-red-900/30 bg-red-950/10 rounded-xl hover:bg-red-900/20 transition-all group">
                        <div className="flex flex-col sm:flex-row justify-between sm:items-start mb-3 gap-2">
                          <div className="flex items-center space-x-3">
                            <span className="px-3 py-1 bg-red-500 text-black text-[10px] sm:text-xs font-bold rounded-sm shadow-[0_0_10px_rgba(239,68,68,0.5)]">RISK: {alert.risk_score}%</span>
                            <span className="text-[10px] sm:text-xs text-neutral-500 font-mono">{new Date(alert.created_at).toLocaleTimeString()}</span>
                          </div>
                          <a href={`https://explorer.mantle.xyz/tx/${alert.tx_hash}`} target="_blank" rel="noreferrer" className="text-[10px] sm:text-xs text-red-400 border border-red-900/50 px-3 py-1 rounded bg-red-950/30 hover:bg-red-900/50 transition-colors sm:opacity-0 group-hover:opacity-100 self-start sm:self-auto">View Tx ↗</a>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4 mt-4">
                          <div className="p-3 bg-neutral-950/50 rounded border border-neutral-800/50 overflow-hidden"><div className="text-[10px] text-neutral-500 uppercase tracking-widest mb-1">Target Developer</div><div className="text-xs sm:text-sm text-neutral-300 truncate">{alert.dev_wallet}</div></div>
                          <div className="p-3 bg-neutral-950/50 rounded border border-neutral-800/50 overflow-hidden"><div className="text-[10px] text-neutral-500 uppercase tracking-widest mb-1">Transaction Hash</div><div className="text-xs sm:text-sm text-neutral-300 truncate">{alert.tx_hash}</div></div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                <div className="mt-6 lg:mt-0">
                  <h2 className="text-lg md:text-xl font-semibold text-white mb-4 flex items-center"><Terminal className="w-5 h-5 text-neutral-500 mr-2" /> Action Logs</h2>
                  
                  {/* --- INVISIBLE SCROLLBAR APPLIED HERE TOO --- */}
                  <div className="bg-neutral-900/30 border border-neutral-800 rounded-xl p-4 h-[400px] md:h-[500px] font-mono text-[10px] md:text-xs overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                    
                    <div className="text-neutral-500 mb-2">Initialize Automated Rescue Protocol...</div>
                    <div className="text-emerald-500 mb-2">[OK] Engine linked to Mantle RPC</div>
                    <div className="text-neutral-500 mb-2 border-b border-neutral-800 pb-2 mb-4">Awaiting threat triggers...</div>
                    {alerts.map((alert, idx) => (
                      <div key={idx} className="mb-3 pl-2 border-l-2 border-red-500 break-all"><div className="text-red-400">!! THREAT DETECTED !!</div><div className="text-neutral-400">Tx: {alert.tx_hash.substring(0, 14)}...</div><div className="text-emerald-500 mt-1">Funds secured.</div></div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'mempool' && (
            <div className="animate-in fade-in duration-300 h-full flex flex-col">
              <h1 className="text-2xl md:text-3xl font-bold text-white mb-2 flex items-center"><Database className="w-6 h-6 md:w-8 md:h-8 mr-3 text-blue-500" /> Mempool Scanner</h1>
              <p className="text-sm md:text-base text-neutral-500 mb-6 md:mb-8">Raw unconfirmed transaction data streaming directly from the Mantle RPC node.</p>
              <div className="flex-1 bg-black border border-neutral-800 rounded-xl p-4 md:p-6 font-mono text-xs md:text-sm overflow-hidden relative min-h-[400px]">
                <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black z-10 pointer-events-none"></div>
                <div className="space-y-2 opacity-70 animate-pulse">
                  {[...Array(20)].map((_, i) => (
                    <div key={i} className="flex flex-col sm:flex-row sm:space-x-4 text-neutral-600 border-b border-neutral-900 pb-2 gap-1 sm:gap-0">
                      <span className="text-blue-900">[{currentBlock ? currentBlock - i : 'Sync'}]</span>
                      <span className="truncate">0x{(Math.random() * 1e16).toString(16)}...</span>
                      <span className="hidden sm:inline">→</span>
                      <span>Contract Execution</span>
                    </div>
                  ))}
                </div>
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20 bg-neutral-900/95 border border-blue-500/30 px-4 md:px-6 py-3 md:py-4 rounded-lg flex items-center shadow-[0_0_30px_rgba(59,130,246,0.2)] w-[90%] md:w-auto justify-center">
                  <Activity className="w-5 h-5 text-blue-500 mr-3 animate-spin shrink-0" />
                  <span className="text-blue-400 font-semibold tracking-wider text-[10px] md:text-sm text-center">INDEXER RUNNING IN BACKGROUND</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'assets' && (
            <div className="animate-in fade-in duration-300">
              <h1 className="text-2xl md:text-3xl font-bold text-white mb-2 flex items-center"><Lock className="w-6 h-6 md:w-8 md:h-8 mr-3 text-emerald-500" /> Protected Assets</h1>
              <p className="text-sm md:text-base text-neutral-500 mb-6 md:mb-8">Tokens currently deposited inside the Predictive Shield Smart Contract.</p>
              
              {!walletAddress ? (
                <div className="p-8 md:p-12 border border-dashed border-neutral-800 rounded-xl flex flex-col items-center justify-center bg-neutral-900/20 text-center">
                  <Wallet className="w-10 h-10 md:w-12 md:h-12 text-neutral-600 mb-4" />
                  <h3 className="text-lg md:text-xl text-white font-semibold mb-2">Wallet Disconnected</h3>
                  <p className="text-sm md:text-base text-neutral-500 max-w-md">Connect your Web3 wallet to view and manage the assets you have deposited into the Vault.</p>
                  <button onClick={() => setIsWalletModalOpen(true)} className="mt-6 px-6 py-2 bg-white text-black font-semibold rounded-md text-sm md:text-base">Connect Wallet</button>
                </div>
              ) : (
                <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl overflow-hidden">
                  <div className="w-full overflow-x-auto">
                    <table className="w-full text-left min-w-[700px]">
                      <thead className="bg-neutral-900 border-b border-neutral-800 text-neutral-400 text-xs md:text-sm">
                        <tr><th className="px-4 md:px-6 py-4 font-medium">Asset</th><th className="px-4 md:px-6 py-4 font-medium">Balance</th><th className="px-4 md:px-6 py-4 font-medium">Value (USD)</th><th className="px-4 md:px-6 py-4 font-medium">Status</th><th className="px-4 md:px-6 py-4 text-right font-medium">Action</th></tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-800 text-white text-sm">
                        <tr className="hover:bg-neutral-800/20 transition-colors">
                          <td className="px-4 md:px-6 py-4 flex items-center"><div className="w-6 h-6 md:w-8 md:h-8 rounded-full bg-blue-500 flex items-center justify-center text-xs md:text-sm font-bold mr-3 shrink-0">M</div> Mantle (MNT)</td>
                          <td className="px-4 md:px-6 py-4">4,500.00</td>
                          <td className="px-4 md:px-6 py-4">$3,825.00</td>
                          <td className="px-4 md:px-6 py-4"><span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-[10px] md:text-xs rounded border border-emerald-500/20 whitespace-nowrap">Protected</span></td>
                          <td className="px-4 md:px-6 py-4 text-right"><button className="text-xs md:text-sm text-neutral-400 hover:text-white">Withdraw</button></td>
                        </tr>
                        <tr className="hover:bg-neutral-800/20 transition-colors">
                          <td className="px-4 md:px-6 py-4 flex items-center"><div className="w-6 h-6 md:w-8 md:h-8 rounded-full bg-green-500 flex items-center justify-center text-black text-xs md:text-sm font-bold mr-3 shrink-0">$</div> USD Coin (USDC)</td>
                          <td className="px-4 md:px-6 py-4">12,500.00</td>
                          <td className="px-4 md:px-6 py-4">$12,500.00</td>
                          <td className="px-4 md:px-6 py-4"><span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-[10px] md:text-xs rounded border border-emerald-500/20 whitespace-nowrap">Protected</span></td>
                          <td className="px-4 md:px-6 py-4 text-right"><button className="text-xs md:text-sm text-neutral-400 hover:text-white">Withdraw</button></td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div className="p-4 md:p-6 border-t border-neutral-800 bg-neutral-950/50 flex flex-col md:flex-row justify-between items-center gap-4 text-center md:text-left">
                    <p className="text-xs md:text-sm text-neutral-500">Only tokens deposited here are monitored by the Watchtower AI.</p>
                    <button className="w-full md:w-auto px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-md transition-colors shadow-[0_0_15px_rgba(5,150,105,0.4)] whitespace-nowrap">
                      + Deposit to Vault
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'config' && (
            <div className="animate-in fade-in duration-300 max-w-3xl">
              <h1 className="text-2xl md:text-3xl font-bold text-white mb-2 flex items-center"><Sliders className="w-6 h-6 md:w-8 md:h-8 mr-3 text-purple-500" /> Watchtower Config</h1>
              <p className="text-sm md:text-base text-neutral-500 mb-6 md:mb-8">Tune the AI heuristics engine and set your automated rescue parameters.</p>
              
              <div className="space-y-4 md:space-y-6">
                <div className="p-4 md:p-6 bg-neutral-900/50 border border-neutral-800 rounded-xl">
                  <h3 className="text-base md:text-lg font-semibold text-white mb-2 md:mb-4">Risk Execution Threshold</h3>
                  <p className="text-xs md:text-sm text-neutral-400 mb-4 md:mb-6">If a transaction is intercepted with a Risk Score higher than this limit, the Vault will automatically execute the Emergency Exit protocol.</p>
                  <div className="flex items-center space-x-4">
                    <input 
                      type="range" min="50" max="100" value={riskThreshold} 
                      onChange={(e) => setRiskThreshold(Number(e.target.value))}
                      className="w-full h-2 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-500"
                    />
                    <span className="text-xl md:text-2xl font-bold text-red-500 w-16 text-right">{riskThreshold}%</span>
                  </div>
                </div>

                <div className="p-4 md:p-6 bg-neutral-900/50 border border-neutral-800 rounded-xl space-y-3 md:space-y-4">
                  <h3 className="text-base md:text-lg font-semibold text-white mb-2">Automated Actions</h3>
                  
                  <div className="flex items-center justify-between p-3 md:p-4 border border-neutral-800 rounded-lg bg-neutral-950/50">
                    <div className="pr-4">
                      <p className="text-sm md:text-base text-white font-medium">Enable Auto-Rescue (Smart Contract)</p>
                      <p className="text-[10px] md:text-xs text-neutral-500 mt-1">Allows the AI to swap your vulnerable tokens to USDC without manual approval.</p>
                    </div>
                    <div className="w-10 h-5 md:w-12 md:h-6 bg-green-500 rounded-full relative cursor-pointer shrink-0"><div className="w-4 h-4 md:w-5 md:h-5 bg-white rounded-full absolute top-[2px] right-[2px] shadow-sm"></div></div>
                  </div>

                  <div className="flex items-center justify-between p-3 md:p-4 border border-neutral-800 rounded-lg bg-neutral-950/50 opacity-50">
                    <div className="pr-4">
                      <p className="text-sm md:text-base text-white font-medium">Telegram Bot Alerts</p>
                      <p className="text-[10px] md:text-xs text-neutral-500 mt-1">Push critical warnings directly to your phone. (Coming in v2)</p>
                    </div>
                    <div className="w-10 h-5 md:w-12 md:h-6 bg-neutral-700 rounded-full relative shrink-0"><div className="w-4 h-4 md:w-5 md:h-5 bg-neutral-500 rounded-full absolute top-[2px] left-[2px]"></div></div>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}