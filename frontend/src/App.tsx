import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Bar, Radar } from 'react-chartjs-2';
import { motion, AnimatePresence } from 'motion/react';
import {
  Activity,
  Bot,
  Download,
  Info,
  RefreshCw,
  Zap,
} from 'lucide-react';
import { GoogleGenAI } from "@google/genai";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

// --- Types ---
interface Stock {
  code: string;
  name: string;
  sec: string;
  fund: number;
  tech: number;
  baseRet: number;
  mir: number;
  simRet: number;
  quintile?: string;
  insight?: string;
}

// --- Constants ---
const STOCKS_DATA: Stock[] = [
  {code:'2330',name:'台積電',  sec:'半導體',    fund:9.2,tech:8.7,baseRet: 5.8, mir: 0, simRet: 0},
  {code:'6669',name:'緯穎',   sec:'伺服器',    fund:8.1,tech:8.9,baseRet: 5.1, mir: 0, simRet: 0},
  {code:'2454',name:'聯發科', sec:'IC設計',    fund:8.5,tech:7.8,baseRet: 4.7, mir: 0, simRet: 0},
  {code:'3034',name:'聯詠',   sec:'IC設計',    fund:7.9,tech:8.2,baseRet: 4.5, mir: 0, simRet: 0},
  {code:'2382',name:'廣達',   sec:'電腦硬體',  fund:7.6,tech:8.1,baseRet: 4.2, mir: 0, simRet: 0},
  {code:'2357',name:'華碩',   sec:'電腦硬體',  fund:7.8,tech:7.5,baseRet: 3.9, mir: 0, simRet: 0},
  {code:'2308',name:'台達電', sec:'電子零組件', fund:7.9,tech:7.2,baseRet: 3.7, mir: 0, simRet: 0},
  {code:'2345',name:'智邦',   sec:'網路設備',  fund:7.2,tech:7.8,baseRet: 3.6, mir: 0, simRet: 0},
  {code:'3008',name:'大立光', sec:'光學',      fund:7.5,tech:7.3,baseRet: 3.4, mir: 0, simRet: 0},
  {code:'1590',name:'亞德客', sec:'工業自動化', fund:7.4,tech:7.2,baseRet: 3.3, mir: 0, simRet: 0},
  {code:'2395',name:'研華',   sec:'工業電腦',  fund:7.1,tech:7.3,baseRet: 3.1, mir: 0, simRet: 0},
  {code:'4938',name:'和碩',   sec:'電子製造',  fund:6.8,tech:7.4,baseRet: 2.9, mir: 0, simRet: 0},
  {code:'2327',name:'國巨',   sec:'電子零組件', fund:7.0,tech:7.0,baseRet: 2.8, mir: 0, simRet: 0},
  {code:'2317',name:'鴻海',   sec:'電子製造',  fund:6.9,tech:6.9,baseRet: 2.6, mir: 0, simRet: 0},
  {code:'3711',name:'日月光投控',sec:'封測',   fund:6.7,tech:7.0,baseRet: 2.5, mir: 0, simRet: 0},
  {code:'2303',name:'聯電',   sec:'半導體',    fund:6.5,tech:7.0,baseRet: 2.3, mir: 0, simRet: 0},
  {code:'2379',name:'瑞昱',   sec:'IC設計',    fund:6.8,tech:6.5,baseRet: 2.2, mir: 0, simRet: 0},
  {code:'2301',name:'光寶科', sec:'電子零組件', fund:6.6,tech:6.6,baseRet: 2.0, mir: 0, simRet: 0},
  {code:'2412',name:'中華電', sec:'電信',      fund:6.4,tech:6.7,baseRet: 1.9, mir: 0, simRet: 0},
  {code:'3045',name:'台灣大', sec:'電信',      fund:6.3,tech:6.5,baseRet: 1.7, mir: 0, simRet: 0},
  {code:'5871',name:'中租-KY',sec:'金融',      fund:6.5,tech:6.1,baseRet: 1.5, mir: 0, simRet: 0},
  {code:'1216',name:'統一',   sec:'食品',      fund:6.2,tech:6.2,baseRet: 1.4, mir: 0, simRet: 0},
  {code:'2881',name:'富邦金', sec:'金融',      fund:6.3,tech:6.0,baseRet: 1.3, mir: 0, simRet: 0},
  {code:'2882',name:'國泰金', sec:'金融',      fund:6.1,tech:6.1,baseRet: 1.1, mir: 0, simRet: 0},
  {code:'2886',name:'兆豐金', sec:'金融',      fund:6.0,tech:6.1,baseRet: 1.0, mir: 0, simRet: 0},
  {code:'1301',name:'台塑',   sec:'石化',      fund:5.8,tech:6.0,baseRet: 0.5, mir: 0, simRet: 0},
  {code:'1303',name:'南亞',   sec:'石化',      fund:5.7,tech:5.9,baseRet: 0.3, mir: 0, simRet: 0},
  {code:'6505',name:'台塑化', sec:'石化',      fund:5.6,tech:5.8,baseRet: 0.1, mir: 0, simRet: 0},
  {code:'2207',name:'和泰車', sec:'汽車',      fund:5.8,tech:5.5,baseRet:-0.1, mir: 0, simRet: 0},
  {code:'2891',name:'中信金', sec:'金融',      fund:5.7,tech:5.5,baseRet:-0.3, mir: 0, simRet: 0},
  {code:'5880',name:'合庫金', sec:'金融',      fund:5.5,tech:5.6,baseRet:-0.5, mir: 0, simRet: 0},
  {code:'9910',name:'豐泰',   sec:'製鞋',      fund:5.4,tech:5.6,baseRet:-0.6, mir: 0, simRet: 0},
  {code:'2884',name:'玉山金', sec:'金融',      fund:5.5,tech:5.4,baseRet:-0.8, mir: 0, simRet: 0},
  {code:'4904',name:'遠傳',   sec:'電信',      fund:5.3,tech:5.3,baseRet:-1.0, mir: 0, simRet: 0},
  {code:'2885',name:'元大金', sec:'金融',      fund:5.2,tech:5.3,baseRet:-1.2, mir: 0, simRet: 0},
  {code:'2892',name:'第一金', sec:'金融',      fund:5.2,tech:5.2,baseRet:-1.3, mir: 0, simRet: 0},
  {code:'2887',name:'台新金', sec:'金融',      fund:5.1,tech:5.2,baseRet:-1.5, mir: 0, simRet: 0},
  {code:'2890',name:'永豐金', sec:'金融',      fund:5.0,tech:5.1,baseRet:-1.7, mir: 0, simRet: 0},
  {code:'2883',name:'開發金', sec:'金融',      fund:4.9,tech:5.0,baseRet:-1.9, mir: 0, simRet: 0},
  {code:'2377',name:'微星',   sec:'電腦硬體',  fund:4.7,tech:5.1,baseRet:-2.1, mir: 0, simRet: 0},
  {code:'8046',name:'南電',   sec:'PCB',       fund:4.8,tech:4.8,baseRet:-2.3, mir: 0, simRet: 0},
  {code:'2002',name:'中鋼',   sec:'鋼鐵',      fund:4.5,tech:4.8,baseRet:-2.6, mir: 0, simRet: 0},
  {code:'1326',name:'台化',   sec:'石化',      fund:4.6,tech:4.5,baseRet:-2.8, mir: 0, simRet: 0},
  {code:'2408',name:'南亞科', sec:'半導體',    fund:4.3,tech:4.6,baseRet:-3.1, mir: 0, simRet: 0},
  {code:'2603',name:'長榮',   sec:'航運',      fund:4.1,tech:4.5,baseRet:-3.4, mir: 0, simRet: 0},
  {code:'2633',name:'台灣高鐵',sec:'運輸',     fund:4.2,tech:4.1,baseRet:-3.6, mir: 0, simRet: 0},
  {code:'2609',name:'陽明',   sec:'航運',      fund:3.8,tech:4.2,baseRet:-4.0, mir: 0, simRet: 0},
  {code:'2615',name:'萬海',   sec:'航運',      fund:3.5,tech:4.0,baseRet:-4.4, mir: 0, simRet: 0},
  {code:'2408-2',name:'南亞科2',sec:'半導體',  fund:3.2,tech:3.6,baseRet:-4.8, mir: 0, simRet: 0},
  {code:'2362',name:'藍天',   sec:'電腦硬體',  fund:3.0,tech:3.2,baseRet:-5.2, mir: 0, simRet: 0},
].map((s, i) => {
  const mir = +(0.5 * s.fund + 0.5 * s.tech).toFixed(2);
  const noise = ((i * 17 + 3) % 11 - 5) * 0.3;
  const simRet = +(s.baseRet + noise).toFixed(2);
  return { ...s, mir, simRet };
});

const Q_COLORS: Record<string, string> = { Q1: '#ef5350', Q2: '#ff9800', Q3: '#9e9e9e', Q4: '#42a5f5', Q5: '#26a69a' };

// --- Helper Functions ---
function assignQuintiles(stocks: Stock[]) {
  const sorted = [...stocks].sort((a, b) => b.mir - a.mir);
  const n = sorted.length;
  const nGroups = Math.min(5, n);
  return sorted.map((s, i) => {
    const q = nGroups > 0 ? Math.min(nGroups, Math.floor(i / (n / nGroups)) + 1) : 1;
    return { ...s, quintile: 'Q' + q };
  });
}

const avgRet = (arr: Stock[]) =>
  arr.length ? +(arr.reduce((a, s) => a + s.simRet, 0) / arr.length).toFixed(2) : 0;

const stdDev = (arr: Stock[]) => {
  if (arr.length < 2) return 0;
  const m = avgRet(arr);
  return +(Math.sqrt(arr.reduce((a, s) => a + (s.simRet - m) ** 2, 0) / (arr.length - 1))).toFixed(2);
};

// --- KPI Component ---
const KPI = ({ label, value, colorClass, sub }: { label: string; value: string; colorClass: string; sub: string }) => (
  <div className="card kpi">
    <div className="lbl">{label}</div>
    <div className={`val ${colorClass}`}>{value}</div>
    <div className="chg text-zinc-500">{sub}</div>
  </div>
);

// --- Main App ---
export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedCodes, setSelectedCodes] = useState<Set<string>>(
    new Set(STOCKS_DATA.map(s => s.code).slice(0, 20))
  );
  const [isScoring, setIsScoring] = useState(false);
  const [scoringProgress, setScoringProgress] = useState(0);
  const [useGemini, setUseGemini] = useState(false);
  const [insights, setInsights] = useState<Record<string, string>>({});
  const [signals, setSignals] = useState<{ id: number; time: string; msg: string; type: 'pos' | 'neg' | 'neu' }[]>([]);
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const signalIdRef = useRef(0);

  const ai = useMemo(() => new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY || '' }), []);

  // Live signal simulation
  useEffect(() => {
    const interval = setInterval(() => {
      const stock = STOCKS_DATA[Math.floor(Math.random() * STOCKS_DATA.length)];
      const types: ('pos' | 'neg' | 'neu')[] = ['pos', 'neg', 'neu'];
      const type = types[Math.floor(Math.random() * types.length)];
      const msgs = {
        pos: [`${stock.name} MIR 評分上調至 Q1`, `${stock.name} 技術面突破壓力線`, `${stock.name} 財報優於預期`],
        neg: [`${stock.name} 跌破季線支撐`, `${stock.name} 基本面評分下修`, `${stock.name} 產業動能轉弱`],
        neu: [`${stock.name} 進入盤整區間`, `${stock.name} 籌碼面維持中性`, `${stock.name} 等待下週法說會`],
      };
      setSignals(prev =>
        [{ id: ++signalIdRef.current, time: new Date().toLocaleTimeString('zh-TW', { hour12: false }), msg: msgs[type][Math.floor(Math.random() * 3)], type }, ...prev].slice(0, 10)
      );
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const scoredStocks = useMemo(() => {
    const active = STOCKS_DATA.filter(s => selectedCodes.has(s.code));
    return assignQuintiles(active).map(s => ({ ...s, insight: insights[s.code] || '' }));
  }, [selectedCodes, insights]);

  const groups = useMemo(() => {
    const g: Record<string, Stock[]> = { Q1: [], Q2: [], Q3: [], Q4: [], Q5: [] };
    scoredStocks.forEach(s => { if (s.quintile && g[s.quintile]) g[s.quintile].push(s); });
    return g;
  }, [scoredStocks]);

  const qRets = useMemo(() => ({
    Q1: avgRet(groups.Q1), Q2: avgRet(groups.Q2), Q3: avgRet(groups.Q3),
    Q4: avgRet(groups.Q4), Q5: avgRet(groups.Q5),
  }), [groups]);

  const lsRet = +(qRets.Q1 - qRets.Q5).toFixed(2);
  const alpha = +(lsRet * 0.43).toFixed(2);

  const runScoring = async () => {
    if (selectedCodes.size === 0) return;
    setIsScoring(true);
    setScoringProgress(0);
    const codesArray = Array.from(selectedCodes);
    for (let i = 0; i < codesArray.length; i++) {
      const code = codesArray[i];
      const stock = STOCKS_DATA.find(s => s.code === code);
      if (useGemini && stock) {
        try {
          const response = await ai.models.generateContent({
            model: 'gemini-2.0-flash',
            contents: `請簡短分析台股股票 ${stock.name} (${stock.code}) 的 MIR 評分。基本面評分: ${stock.fund}, 技術面評分: ${stock.tech}。請給出 20 字以內的投資建議。`,
          });
          setInsights(prev => ({ ...prev, [code]: response.text || '分析完成' }));
        } catch (e) {
          console.error('Gemini Error:', e);
        }
      }
      setScoringProgress(i + 1);
      await new Promise(r => setTimeout(r, useGemini ? 100 : 20));
    }
    setIsScoring(false);
  };

  const exportToCSV = () => {
    const headers = ['排名', '代碼', '公司', '產業', '基本面', '技術面', 'MIR', '五分位', 'AI 建議'];
    const rows = scoredStocks.map((s, i) => [
      i + 1, s.code, s.name, s.sec, s.fund, s.tech, s.mir, s.quintile, s.insight?.replace(/,/g, ' ') || '',
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MIR_Scores_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#9090b0', font: { size: 10 } } } },
    scales: {
      x: { ticks: { color: '#9090b0' }, grid: { display: false } },
      y: { ticks: { color: '#9090b0' }, grid: { color: 'rgba(255,255,255,.06)' } },
    },
  };

  const steps = [
    { sn: 'INPUT A',  st: '📄 財務報表',   sd: '最近4季季報\n獲利／槓桿／成長\n匿名化處理',    detail: '從公開資訊觀測站抓取最新財報，並將公司名稱匿名化，避免 LLM 產生品牌偏誤。' },
    { sn: 'MODULE 1', st: '🧮 基本面模組', sd: 'LLM 文字評分\nROE/ROA/毛利率\n負債比/成長率', color: '#6c63ff', detail: '利用 Gemini AI 分析獲利能力、償債能力與經營效率，給出 1-10 分的綜合評分。' },
    { sn: 'INPUT B',  st: '📉 技術圖表',   sd: '1年日線K線圖\nMACD/KD/量\n匿名化處理',        detail: '將股價走勢圖轉換為 Base64 圖片，由多模態模型進行視覺化趨勢分析。' },
    { sn: 'MODULE 2', st: '📊 技術模組',   sd: 'LLM 視覺評分\n趨勢/動能/KD\n量價配合',        color: '#ff6584', detail: 'AI 辨識型態（如頭肩底、W底）並結合技術指標動能，給出 1-10 分的技術評分。' },
    { sn: 'OUTPUT',   st: '🏆 MIR 分數',   sd: '加權整合評分\nQ1（最佳）～Q5\n每季末重新排名', color: '#43e97b', detail: '將基本面與技術面分數加權平均，產生最終 MIR 分數，並進行全市場五分位排名。' },
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-[#1a1d2e] border-b border-[#2e3058] p-4 px-7 flex items-center gap-3 sticky top-0 z-50">
        <h1 className="text-xl font-bold text-[#6c63ff]">🧠 台股 MIR 系統</h1>
        <span className="text-[11px] text-[#9090b0] bg-[#252840] px-2 py-0.5 rounded-full">Machine Insight Rating</span>
        <span className="text-[11px] text-[#9090b0] bg-[#252840] px-2 py-0.5 rounded-full">基於 Shyu (2026)</span>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-[11px] text-[#9090b0]">示範資料</span>
          <div className="w-2 h-2 rounded-full bg-[#43e97b] animate-pulse" />
          <span className="text-xs text-[#9090b0]">
            {isScoring ? `評分中 ${scoringProgress}/${selectedCodes.size}` : '就緒'}
          </span>
        </div>
      </header>

      <div className="max-w-[1400px] mx-auto p-7">
        {/* Tabs */}
        <div className="tabs mb-5">
          {[
            { id: 'dashboard', label: '📊 總覽' },
            { id: 'scoring',   label: '🤖 MIR 評分' },
            { id: 'portfolio', label: '📈 投組分析' },
            { id: 'factor',    label: '📐 因子模型' },
            { id: 'guide',     label: '📖 說明' },
          ].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} className={`tab ${activeTab === t.id ? 'active' : ''}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* ── Dashboard ── */}
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-5">
            <div className="xl:col-span-3 space-y-5">
              {/* KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                <KPI label="長短組合季報酬（Q1−Q5）" value={`${lsRet >= 0 ? '+' : ''}${lsRet}%`} colorClass={lsRet >= 0 ? 'pos' : 'neg'} sub="依目前選股計算" />
                <KPI label="FF5 Alpha（季）" value={`${alpha >= 0 ? '+' : ''}${alpha}%`} colorClass={alpha >= 0 ? 'pos' : 'neg'} sub="t = 2.41 *" />
                <KPI label="目前選股數" value={selectedCodes.size.toString()} colorClass="text-[#6c63ff]" sub="台灣50成分股" />
                <KPI label="樣本期間" value="2010–2024" colorClass="text-[#6c63ff]" sub="共59季" />
              </div>

              {/* Flow diagram */}
              <div className="card">
                <div className="ct flex justify-between items-center">
                  <div className="flex items-center gap-2"><span className="dot bg-[#6c63ff]" />MIR 評分架構</div>
                  <div className="text-[10px] text-zinc-500 flex items-center gap-1"><Info size={12} /> 點擊步驟查看詳情</div>
                </div>
                <div className="flow">
                  {steps.map((step, i) => (
                    <React.Fragment key={i}>
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className={`fstep cursor-pointer transition-all ${activeStep === i ? 'ring-2 ring-white scale-105 bg-[#2e3058]' : ''}`}
                        style={step.color ? { borderColor: step.color } : {}}
                        onClick={() => setActiveStep(activeStep === i ? null : i)}
                      >
                        <div className="sn">{step.sn}</div>
                        <div className="st">{step.st}</div>
                        <div className="sd whitespace-pre-line">{step.sd}</div>
                      </motion.div>
                      {i < 4 && <div className="farr">→</div>}
                    </React.Fragment>
                  ))}
                </div>
                <AnimatePresence>
                  {activeStep !== null && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-4 p-3 bg-[#252840] rounded border border-[#2e3058] text-xs text-[#9090b0]">
                        <strong className="text-white block mb-1">💡 詳情：</strong>
                        {steps[activeStep].detail}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <div className="card h-[300px]">
                  <div className="ct"><span className="dot bg-[#6c63ff]" />各五分位平均季報酬</div>
                  <Bar options={chartOptions} data={{
                    labels: ['Q1','Q2','Q3','Q4','Q5'],
                    datasets: [{ data: [qRets.Q1,qRets.Q2,qRets.Q3,qRets.Q4,qRets.Q5], backgroundColor: Object.values(Q_COLORS) }],
                  }} />
                </div>
                <div className="card h-[300px]">
                  <div className="ct"><span className="dot bg-[#ff6584]" />三模組 Long-Short Alpha 比較</div>
                  <Bar options={chartOptions} data={{
                    labels: ['基本面','技術面','整合 MIR'],
                    datasets: [{ data: [+(alpha*0.82).toFixed(2), +(alpha*0.69).toFixed(2), alpha], backgroundColor: ['#6c63ff','#ff6584','#43e97b'] }],
                  }} />
                </div>
              </div>
            </div>

            {/* Signal feed */}
            <div className="space-y-5">
              <div className="card h-full flex flex-col" style={{ minHeight: '500px' }}>
                <div className="ct flex items-center gap-2"><Activity size={16} className="text-[#43e97b]" />即時訊號流</div>
                <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin">
                  {signals.length === 0 && (
                    <div className="text-center text-zinc-600 py-10 text-xs">等待市場訊號...</div>
                  )}
                  <AnimatePresence initial={false}>
                    {signals.map(sig => (
                      <motion.div
                        key={sig.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="p-2 bg-[#252840] rounded border-l-2 border-[#2e3058]"
                      >
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-[10px] font-mono text-zinc-500">{sig.time}</span>
                          <span className={`text-[9px] px-1 rounded ${sig.type === 'pos' ? 'bg-emerald-500/20 text-emerald-400' : sig.type === 'neg' ? 'bg-rose-500/20 text-rose-400' : 'bg-zinc-500/20 text-zinc-400'}`}>
                            {sig.type === 'pos' ? '看多' : sig.type === 'neg' ? '看空' : '中性'}
                          </span>
                        </div>
                        <div className="text-xs text-zinc-300">{sig.msg}</div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Scoring ── */}
        {activeTab === 'scoring' && (
          <div className="space-y-5">
            <div className="apib">
              <div className="flex items-center gap-3">
                <Bot className={useGemini ? 'text-[#43e97b]' : 'text-zinc-500'} />
                <div>
                  <div className="text-sm font-semibold mb-1">🤖 Gemini AI 深度分析</div>
                  <div className="text-[11px] text-[#9090b0]">啟用後評分過程將調用 LLM 生成質性建議</div>
                </div>
              </div>
              <div className="flex-1" />
              <button onClick={() => setUseGemini(!useGemini)} className={`btn ${useGemini ? 'bp' : 'bs'}`}>
                {useGemini ? '已啟用' : '已停用'}
              </button>
            </div>

            <div className="card">
              <div className="shdr">
                <div>
                  <h2>選擇評分股票</h2>
                  <p>點選加入評分（目前已選 {selectedCodes.size} 檔）</p>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <button className="btn bs" onClick={() => setSelectedCodes(new Set(STOCKS_DATA.map(s => s.code)))}>全選</button>
                  <button className="btn bs" onClick={() => setSelectedCodes(new Set())}>清除</button>
                  <button className="btn bp flex items-center gap-2" onClick={runScoring} disabled={isScoring}>
                    {isScoring ? <RefreshCw size={14} className="animate-spin" /> : <Zap size={14} />}
                    ▶ 執行評分
                  </button>
                </div>
              </div>
              <div className="tg">
                {STOCKS_DATA.map(s => (
                  <div
                    key={s.code}
                    className={`chip ${selectedCodes.has(s.code) ? 'sel' : ''}`}
                    onClick={() => {
                      const next = new Set(selectedCodes);
                      next.has(s.code) ? next.delete(s.code) : next.add(s.code);
                      setSelectedCodes(next);
                    }}
                  >
                    <div>{s.code}</div>
                    <div className="cn">{s.name}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card overflow-x-auto">
              <div className="ct flex justify-between items-center">
                <div className="flex items-center gap-2"><span className="dot bg-[#43e97b]" />MIR 評分結果</div>
                <button className="btn bs flex items-center gap-2 text-[10px] py-1" onClick={exportToCSV}>
                  <Download size={12} />匯出 CSV
                </button>
              </div>
              <table className="tbl">
                <thead>
                  <tr>
                    <th>排名</th><th>代碼</th><th>公司</th><th>產業</th>
                    <th>基本面</th><th>技術面</th><th>MIR</th><th>五分位</th><th>AI 建議</th>
                  </tr>
                </thead>
                <tbody>
                  {scoredStocks.map((s, i) => (
                    <tr key={s.code}>
                      <td>{i + 1}</td>
                      <td className="text-[#6c63ff] font-mono">{s.code}.TW</td>
                      <td className="font-semibold">{s.name}</td>
                      <td className="text-[11px] text-[#9090b0]">{s.sec}</td>
                      <td>
                        <div className="sbar">
                          <div className="bg"><div className="fill bg-[#6c63ff]" style={{ width: `${s.fund * 10}%` }} /></div>
                          <span className="num">{s.fund}</span>
                        </div>
                      </td>
                      <td>
                        <div className="sbar">
                          <div className="bg"><div className="fill bg-[#ff6584]" style={{ width: `${s.tech * 10}%` }} /></div>
                          <span className="num">{s.tech}</span>
                        </div>
                      </td>
                      <td className="font-bold text-lg" style={{ color: s.quintile ? Q_COLORS[s.quintile] : 'inherit' }}>{s.mir}</td>
                      <td><span className={`bdg bq${s.quintile?.slice(1)}`}>{s.quintile}</span></td>
                      <td className="text-[11px] text-zinc-400 italic max-w-[200px] truncate" title={s.insight}>{s.insight || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Portfolio ── */}
        {activeTab === 'portfolio' && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {(['Q1','Q2','Q3','Q4','Q5'] as const).map(q => (
                <KPI key={q} label={`${q} 平均季報酬`}
                  value={`${qRets[q] >= 0 ? '+' : ''}${qRets[q]}%`}
                  colorClass={qRets[q] >= 0 ? 'pos' : 'neg'} sub="模擬數據" />
              ))}
              <KPI label="Q1−Q5 Spread" value={`${lsRet >= 0 ? '+' : ''}${lsRet}%`}
                colorClass={lsRet >= 0 ? 'pos' : 'neg'} sub="多空組合" />
            </div>
            <div className="card overflow-x-auto">
              <div className="ct"><span className="dot bg-[#43e97b]" />投組績效摘要</div>
              <table className="tbl">
                <thead>
                  <tr>
                    <th>投資組合</th><th className="r">股票數</th><th className="r">平均 MIR</th>
                    <th className="r">模擬季報酬</th><th className="r">標準差</th><th className="r">Sharpe</th><th className="r">勝率</th>
                  </tr>
                </thead>
                <tbody>
                  {['Q1','Q2','Q3','Q4','Q5'].map(q => {
                    const arr = groups[q];
                    const r = qRets[q as keyof typeof qRets];
                    const sd = stdDev(arr);
                    return (
                      <tr key={q}>
                        <td><span className={`bdg bq${q.slice(1)}`}>{q}</span></td>
                        <td className="r">{arr.length}</td>
                        <td className="r">{arr.length ? (arr.reduce((a,s)=>a+s.mir,0)/arr.length).toFixed(2) : '-'}</td>
                        <td className={`r font-bold ${r >= 0 ? 'pos' : 'neg'}`}>{r >= 0 ? '+' : ''}{r}%</td>
                        <td className="r">{sd}%</td>
                        <td className="r">{sd ? ((r - 0.375) / sd).toFixed(2) : '-'}</td>
                        <td className="r">{arr.length ? Math.round(arr.filter(s=>s.simRet>0).length/arr.length*100) : 0}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Factor ── */}
        {activeTab === 'factor' && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="card h-[350px]">
                <div className="ct"><span className="dot bg-[#6c63ff]" />Alpha 各模型比較</div>
                <Bar options={chartOptions} data={{
                  labels: ['CAPM','FF3','FF5','FF5+MOM'],
                  datasets: [{ label: 'Alpha (季%)', data: [+(alpha*1.13).toFixed(2),+(alpha*1.06).toFixed(2),alpha,+(alpha*0.97).toFixed(2)], backgroundColor: '#6c63ff' }],
                }} />
              </div>
              <div className="card h-[350px]">
                <div className="ct"><span className="dot bg-[#ff6584]" />因子暴露 (FF5 Beta)</div>
                <Radar
                  options={{ ...chartOptions, scales: { r: { ticks: { display: false }, grid: { color: 'rgba(255,255,255,.1)' } } } }}
                  data={{
                    labels: ['市場β','SMB','HML','RMW','CMA','MOM'],
                    datasets: [
                      { label: 'Q1', data: [0.88,0.12,0.21,-0.05,0.09,0.18], borderColor: '#ef5350', backgroundColor: 'rgba(239,83,80,.1)' },
                      { label: 'Q5', data: [1.02,-0.08,-0.18,0.09,-0.13,-0.22], borderColor: '#26a69a', backgroundColor: 'rgba(38,166,154,.1)' },
                    ],
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Guide ── */}
        {activeTab === 'guide' && (
          <div className="card">
            <div className="ct"><span className="dot bg-[#6c63ff]" />快速開始</div>
            <pre className="bg-[#252840] p-4 rounded-lg text-[#a8d8ea] text-xs leading-relaxed overflow-x-auto">
{`# 安裝套件
pip install -r requirements.txt

# 設定 API Key
export ANTHROPIC_API_KEY=sk-ant-...

# 示範模式（5檔 × 2季）
python 00_main_pipeline.py --mode demo

# 完整執行（台灣50 × 59季）
python 00_main_pipeline.py --mode full`}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
