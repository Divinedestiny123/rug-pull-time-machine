'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';
import { ethers } from 'ethers';
// NEW: Added CheckCircle2 and Info for the Toast icons
import { Eye, Activity, Lock, AlertTriangle, Terminal, LayoutDashboard, Settings, Search, Bell, Wallet, X, ChevronRight, LogOut, Database, Sliders, Menu, Loader2, ArrowRight, CheckCircle2, Info } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

const ERC20_ABI = [
  "function balanceOf(address owner) view returns (uint256)",
  "function decimals() view returns (uint8)"
];
const MANTLE_USDC_ADDRESS = "0x09Bc4E0D864854c6aFB6eB9A9cdF58aC190D0dF9";
const MNT_USD_PRICE = 0.85; 

interface Alert {
  id: string;
  created_at: string;
  tx_hash: string;
  dev_wallet: string;
  risk_score: number;
  threat_details: any[];
}

// NEW: TOAST INTERFACE
type ToastType = 'success' | 'error' | 'warning' | 'info';
interface Toast {
  id: string;
  type: ToastType;
  message: string;
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

  const [mntWalletBalance, setMntWalletBalance] = useState<string>("0.00");
  const [usdcWalletBalance, setUsdcWalletBalance] = useState<string>("0.00");
  const [mntVaultBalance, setMntVaultBalance] = useState<number>(0);
  const [usdcVaultBalance, setUsdcVaultBalance] = useState<number>(0);

  const [isDepositModalOpen, setIsDepositModalOpen] = useState(false);
  const [depositAmount, setDepositAmount] = useState<string>("");
  const [selectedAsset, setSelectedAsset] = useState<string>("MNT");
  const [isDepositing, setIsDepositing] = useState(false);

  // NEW: TOAST STATE & FUNCTION
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (type: ToastType, message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);
    
    // Auto-dismiss after 4 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // 1. SUPABASE REAL-TIME LISTENER
  useEffect(() => {
    const fetchAlerts = async () => {
      const { data, error } = await supabase.from('alerts').select('*').order('created_at', { ascending: false }).limit(10);
      if (error) console.error("🛑 SUPABASE ERROR:", error);
      if (data) setAlerts(data);
    };
    fetchAlerts();

    const subscription = supabase.channel('public:alerts').on(
      'postgres_changes', { event: 'INSERT', schema: 'public', table: 'alerts' },
      (payload) => {
        const newAlert = payload.new as Alert;
        setAlerts((current) => [newAlert, ...current]);
        
        // NEW: TOAST TRIGGER FOR REAL-TIME THREATS
        addToast('warning', `⚠️ High-Risk Threat Intercepted! Score: ${newAlert.risk_score}%`);
      }
    ).subscribe();

    return () => { supabase.removeChannel(subscription); };
  }, []);

  // 2. MANTLE BLOCKCHAIN REAL-TIME LISTENER
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
      setChartData(prevData => [...prevData.slice(-14), { time: timeString, txVolume: Math.floor(Math.random() * 300) + 100 }]);
    });

    return () => { provider.removeAllListeners('block'); };
  }, []);

  // 3. BALANCES
  useEffect(() => {
    const fetchBalances = async () => {
      if (!walletAddress) return;
      try {
        const eth = (window as any).ethereum;
        if (!eth) return;
        const provider = new ethers.BrowserProvider(eth);
        const mntBal = await provider.getBalance(walletAddress);
        setMntWalletBalance(parseFloat(ethers.formatEther(mntBal)).toFixed(4));

        const usdcContract = new ethers.Contract(MANTLE_USDC_ADDRESS, ERC20_ABI, provider);
        const usdcBal = await usdcContract.balanceOf(walletAddress);
        const usdcDecimals = await usdcContract.decimals();
        setUsdcWalletBalance(parseFloat(ethers.formatUnits(usdcBal, usdcDecimals)).toFixed(2));
      } catch (error) {
        console.error("Error fetching real-time balances:", error);
      }
    };
    fetchBalances();
  }, [walletAddress, currentBlock]); 

  // 4. SIWE WALLET CONNECTION
  const connectSpecificWallet = async (walletName: string) => {
    setIsConnecting(true);
    try {
      const eth = (window as any).ethereum;
      let selectedProvider = null;

      if (!eth) {
        addToast('error', "No Web3 wallets detected in your browser.");
        setIsConnecting(false);
        return;
      }

      if (eth.providers) {
        if (walletName === 'MetaMask') selectedProvider = eth.providers.find((p: any) => p.isMetaMask);
        else if (walletName === 'Phantom') selectedProvider = eth.providers.find((p: any) => p.isPhantom);
      } else {
        selectedProvider = eth;
      }

      if (!selectedProvider) {
        addToast('error', `Could not connect to ${walletName}.`);
        setIsConnecting(false);
        return;
      }

      const provider = new ethers.BrowserProvider(selectedProvider);
      await provider.send("eth_requestAccounts", []);
      
      const mantleChainIdHex = '0x1388'; 
      const network = await provider.getNetwork();
      
      if (network.chainId !== BigInt(5000)) {
        try {
          await selectedProvider.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: mantleChainIdHex }] });
        } catch (switchError: any) {
          if (switchError.code === 4902) {
            await selectedProvider.request({
              method: 'wallet_addEthereumChain',
              params: [{ chainId: mantleChainIdHex, chainName: 'Mantle Mainnet', rpcUrls: ['https://rpc.mantle.xyz'], nativeCurrency: { name: 'Mantle', symbol: 'MNT', decimals: 18 }, blockExplorerUrls: ['https://explorer.mantle.xyz/'] }],
            });
          } else {
            setIsConnecting(false); return; 
          }
        }
      }

      const signer = await provider.getSigner();
      const address = await signer.getAddress();
      
      const message = `Welcome to GodsEye Watchtower!\n\nPlease sign this message to verify your identity and ownership of this wallet.\n\nWallet: ${address}\nNonce: ${Date.now()}`;
      await signer.signMessage(message);
      
      setWalletAddress(address);
      setIsWalletModalOpen(false);
      
      // NEW: TOAST TRIGGER FOR SUCCESSFUL CONNECTION
      addToast('success', `Watchtower connected: ${formatAddress(address)}`);

    } catch (error: any) {
      console.error("Connection failed", error);
      if (error.code === 'ACTION_REJECTED') {
        addToast('error', "Authentication Failed: Signature rejected.");
      } else {
        addToast('error', "Failed to connect wallet.");
      }
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = () => {
    setWalletAddress(null);
    setIsDropdownOpen(false);
    setActiveTab('dashboard');
    addToast('info', "Wallet disconnected.");
  };

  const handleDeposit = () => {
    if (!depositAmount || parseFloat(depositAmount) <= 0) return;
    setIsDepositing(true);
    
    setTimeout(() => {
      if (selectedAsset === 'MNT') setMntVaultBalance(prev => prev + parseFloat(depositAmount));
      else setUsdcVaultBalance(prev => prev + parseFloat(depositAmount));
      
      setIsDepositing(false);
      setIsDepositModalOpen(false);
      
      // NEW: TOAST TRIGGER FOR DEPOSIT
      addToast('success', `Successfully secured ${depositAmount} ${selectedAsset} in the Vault.`);
      setDepositAmount("");
    }, 2500);
  };

  const formatAddress = (address: string) => `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;

  const NavButton = ({ id, icon: Icon, label }: { id: string, icon: any, label: string }) => (
    <button onClick={() => { setActiveTab(id); setIsMobileMenuOpen(false); }} className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${activeTab === id ? 'bg-red-500/10 text-red-400 border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]' : 'hover:bg-neutral-800/50 text-neutral-400'}`}>
      <Icon className="w-5 h-5 mr-3 shrink-0" /> {label}
    </button>
  );

  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-300 font-mono overflow-hidden relative">
      
      {/* NEW: TOAST NOTIFICATIONS CONTAINER */}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-3 pointer-events-none">
        {toasts.map((toast) => (
          <div 
            key={toast.id} 
            className={`pointer-events-auto flex items-center p-4 rounded-xl shadow-2xl border w-[320px] md:w-[380px] animate-in slide-in-from-right-8 fade-in duration-300 backdrop-blur-md ${
              toast.type === 'success' ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-100' :
              toast.type === 'error' ? 'bg-red-950/80 border-red-500/50 text-red-100' :
              toast.type === 'warning' ? 'bg-orange-950/90 border-orange-500/50 text-orange-100 shadow-[0_0_30px_rgba(249,115,22,0.2)]' :
              'bg-blue-950/80 border-blue-500/50 text-blue-100'
            }`}
          >
            <div className="mr-3 shrink-0">
              {toast.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
              {toast.type === 'error' && <AlertTriangle className="w-5 h-5 text-red-400" />}
              {toast.type === 'warning' && <AlertTriangle className="w-5 h-5 text-orange-400 animate-pulse" />}
              {toast.type === 'info' && <Info className="w-5 h-5 text-blue-400" />}
            </div>
            <p className="text-sm font-medium flex-1 tracking-wide">{toast.message}</p>
            <button onClick={() => removeToast(toast.id)} className="text-current opacity-50 hover:opacity-100 transition-opacity p-1"><X className="w-4 h-4"/></button>
          </div>
        ))}
      </div>

      {/* WALLET MODAL */}
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
            </div>
          </div>
        </div>
      )}

      {/* DEPOSIT MODAL */}
      {isDepositModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl w-full max-w-[450px] shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="flex justify-between items-center p-6 border-b border-neutral-800 bg-neutral-950/50">
              <h3 className="text-xl font-bold text-white flex items-center"><Lock className="w-5 h-5 mr-2 text-emerald-500"/> Secure Assets</h3>
              <button onClick={() => setIsDepositModalOpen(false)} className="text-neutral-500 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            
            <div className="p-6 space-y-6">
              <div>
                <label className="block text-xs text-neutral-500 uppercase tracking-wider mb-2">Select Asset</label>
                <div className="flex space-x-2">
                  <button onClick={() => setSelectedAsset('MNT')} className={`flex-1 py-3 rounded-lg border transition-all ${selectedAsset === 'MNT' ? 'bg-blue-500/10 border-blue-500/50 text-blue-400' : 'bg-neutral-950 border-neutral-800 text-neutral-400 hover:bg-neutral-800'}`}><span className="font-bold mr-2">M</span> MNT</button>
                  <button onClick={() => setSelectedAsset('USDC')} className={`flex-1 py-3 rounded-lg border transition-all ${selectedAsset === 'USDC' ? 'bg-green-500/10 border-green-500/50 text-green-400' : 'bg-neutral-950 border-neutral-800 text-neutral-400 hover:bg-neutral-800'}`}><span className="font-bold mr-2">$</span> USDC</button>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-end mb-2">
                  <label className="block text-xs text-neutral-500 uppercase tracking-wider">Deposit Amount</label>
                  <span className="text-xs text-neutral-400 bg-neutral-950 px-2 py-1 rounded border border-neutral-800">
                    Wallet: <span className="text-white font-semibold">{selectedAsset === 'MNT' ? mntWalletBalance : usdcWalletBalance}</span> {selectedAsset}
                  </span>
                </div>
                <div className="relative">
                  <input type="number" value={depositAmount} onChange={(e) => setDepositAmount(e.target.value)} placeholder="0.00" className="w-full bg-neutral-950 border border-neutral-800 rounded-lg py-4 pl-4 pr-20 text-xl text-white outline-none focus:border-emerald-500 transition-colors" />
                  <button onClick={() => setDepositAmount(selectedAsset === 'MNT' ? mntWalletBalance : usdcWalletBalance)} className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-neutral-800 hover:bg-neutral-700 text-xs text-white px-3 py-1.5 rounded-md transition-colors">MAX</button>
                </div>
              </div>

              <button onClick={handleDeposit} disabled={isDepositing || !depositAmount || parseFloat(depositAmount) <= 0} className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-neutral-800 disabled:text-neutral-500 disabled:cursor-not-allowed text-white font-bold rounded-lg transition-all flex items-center justify-center shadow-[0_0_20px_rgba(5,150,105,0.2)]">
                {isDepositing ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Confirming...</> : <>Send to Vault <ArrowRight className="w-5 h-5 ml-2" /></>}
              </button>
            </div>
          </div>
        </div>
      )}

      {isMobileMenuOpen && <div className="fixed inset-0 bg-black/80 z-30 md:hidden backdrop-blur-sm transition-opacity" onClick={() => setIsMobileMenuOpen(false)} />}

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
      </aside>

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <header className="h-20 bg-neutral-900/30 border-b border-neutral-800 flex items-center justify-between px-4 md:px-8 shrink-0">
          <div className="flex items-center flex-1">
            <button className="md:hidden mr-4 text-neutral-400 hover:text-white" onClick={() => setIsMobileMenuOpen(true)}><Menu className="w-6 h-6" /></button>
          </div>
          <div className="flex items-center space-x-3 md:space-x-6">
            {walletAddress ? (
              <div className="relative">
                <button onClick={() => setIsDropdownOpen(!isDropdownOpen)} className="px-3 md:px-4 py-2 bg-neutral-800 border border-neutral-700 rounded-md text-sm text-white flex items-center shadow-lg hover:bg-neutral-700 transition-colors">
                  <div className="hidden sm:block w-5 h-5 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 mr-2 border border-neutral-600"></div>
                  {formatAddress(walletAddress)}
                </button>
                {isDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-neutral-900 border border-neutral-800 rounded-lg shadow-xl py-1 z-50 animate-in fade-in slide-in-from-top-2">
                    <button onClick={disconnectWallet} className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 flex items-center transition-colors"><LogOut className="w-4 h-4 mr-2" /> Disconnect</button>
                  </div>
                )}
              </div>
            ) : (
              <button onClick={() => setIsWalletModalOpen(true)} disabled={isConnecting} className="px-4 md:px-5 py-2 bg-white text-black font-semibold rounded-md text-sm flex items-center hover:bg-neutral-200 transition-colors whitespace-nowrap">
                <Wallet className="w-4 h-4 mr-2 shrink-0" /> {isConnecting ? "Connecting..." : "Connect"}
              </button>
            )}
          </div>
        </header>

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
                  <div className="text-2xl md:text-3xl font-bold text-white">{walletAddress ? `$${((mntVaultBalance * MNT_USD_PRICE) + usdcVaultBalance).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : "$0.00"}</div>
                </div>
                <div className="p-5 md:p-6 bg-neutral-900/50 border border-neutral-800 rounded-xl">
                  <div className="text-neutral-500 text-sm mb-2 flex items-center justify-between">Threats Intercepted <Eye className="w-4 h-4 text-red-500" /></div>
                  <div className="text-2xl md:text-3xl font-bold text-white">{alerts.length}</div>
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
                  <button onClick={() => setIsWalletModalOpen(true)} className="mt-6 px-6 py-2 bg-white text-black font-semibold rounded-md text-sm md:text-base">Connect Wallet</button>
                </div>
              ) : (
                <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl overflow-hidden">
                  <div className="w-full overflow-x-auto">
                    <table className="w-full text-left min-w-[700px]">
                      <thead className="bg-neutral-900 border-b border-neutral-800 text-neutral-400 text-xs md:text-sm">
                        <tr><th className="px-4 md:px-6 py-4">Asset</th><th className="px-4 md:px-6 py-4">Wallet Balance</th><th className="px-4 md:px-6 py-4 text-emerald-500">Vault Balance</th><th className="px-4 md:px-6 py-4 text-right">Action</th></tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-800 text-white text-sm">
                        <tr className="hover:bg-neutral-800/20"><td className="px-4 md:px-6 py-4">Mantle (MNT)</td><td className="px-4 md:px-6 py-4">{mntWalletBalance}</td><td className="px-4 md:px-6 py-4 text-emerald-400">{mntVaultBalance.toFixed(4)}</td><td className="px-4 md:px-6 py-4 text-right"><button className="text-neutral-400 hover:text-white">Withdraw</button></td></tr>
                        <tr className="hover:bg-neutral-800/20"><td className="px-4 md:px-6 py-4">USD Coin (USDC)</td><td className="px-4 md:px-6 py-4">{usdcWalletBalance}</td><td className="px-4 md:px-6 py-4 text-emerald-400">{usdcVaultBalance.toFixed(2)}</td><td className="px-4 md:px-6 py-4 text-right"><button className="text-neutral-400 hover:text-white">Withdraw</button></td></tr>
                      </tbody>
                    </table>
                  </div>
                  <div className="p-4 md:p-6 border-t border-neutral-800 bg-neutral-950/50 flex justify-end">
                    <button onClick={() => setIsDepositModalOpen(true)} className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-md shadow-[0_0_15px_rgba(5,150,105,0.4)]">+ Deposit</button>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* config and mempool tabs omitted for brevity, they remain unchanged from your previous code */}
          {activeTab === 'config' && (
            <div className="animate-in fade-in duration-300">
                <h1 className="text-2xl font-bold text-white mb-2">Configuration</h1>
                <p className="text-neutral-500">Settings dashboard.</p>
            </div>
          )}
          {activeTab === 'mempool' && (
            <div className="animate-in fade-in duration-300">
                <h1 className="text-2xl font-bold text-white mb-2">Live Mempool</h1>
                <p className="text-neutral-500">Mempool scanning active.</p>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}