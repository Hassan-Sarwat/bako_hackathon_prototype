import React, { useState, useEffect, useRef } from 'react';
import { Settings, BarChart2, Briefcase, Wrench, ClipboardCheck, Mic, MicOff } from 'lucide-react';
import { VoiceSession } from './voice_session';

const shortcuts = [
  { icon: <Briefcase size={24} className="text-[#4A7C7A]" />, label: 'Bestellung', bgColor: '#D1F2F2' },
  { icon: <Wrench size={24} className="text-[#A32A2A]" />, label: 'Wartung', bgColor: '#FCE8E8' },
  { icon: <ClipboardCheck size={24} className="text-[#4A3728]" />, label: 'Prüfung', bgColor: '#E8E6D8' },
];

const App = () => {
  const [active, setActive] = useState(false);
  const [status, setStatus] = useState('disconnected');
  const [transcript, setTranscript] = useState('');
  const voiceSessionRef = useRef(null);

  const toggleVoice = async () => {
    if (active) {
      voiceSessionRef.current?.stop();
      setActive(false);
    } else {
      const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
      if (!apiKey) {
        alert('Please set VITE_GEMINI_API_KEY in .env');
        return;
      }
      
      voiceSessionRef.current = new VoiceSession(
        apiKey,
        'alice', // Example staff ID
        (text) => setTranscript(text),
        (newStatus) => setStatus(newStatus)
      );
      
      try {
        await voiceSessionRef.current.start();
        setActive(true);
      } catch (err) {
        console.error(err);
        setStatus('error');
      }
    }
  };

  useEffect(() => {
    return () => {
      voiceSessionRef.current?.stop();
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#FAF9F6] flex flex-col items-center p-6 font-sans text-[#4A3728]">
      {/* Header */}
      <header className="w-full max-w-md flex justify-between items-center mb-8">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-[#E8DCC4]">
            <img 
              src="/img.avif" 
              alt="Chef Portrait" 
              className="object-cover"
            />
          </div>
          <h1 className="text-xl font-bold tracking-tight">Bernd das Brot</h1>
        </div>
        <button className="p-2 hover:bg-stone-200 rounded-full transition-colors">
          <Settings size={24} className="text-[#4A3728]" />
        </button>
      </header>

      {/* Status Pill */}
      <div className="bg-[#F0F0EA] px-6 py-2 rounded-full flex items-center gap-3 mb-12 shadow-sm border border-stone-100">
        <div className="flex items-end gap-[2px] h-4">
          <div className={`w-1 h-2/3 rounded-full ${status === 'connected' ? 'bg-[#4A7C7A] animate-pulse' : 'bg-stone-400'}`}></div>
          <div className={`w-1 h-full rounded-full ${status === 'connected' ? 'bg-[#4A7C7A] animate-pulse delay-75' : 'bg-stone-400'}`}></div>
          <div className={`w-1 h-1/2 rounded-full ${status === 'connected' ? 'bg-[#4A7C7A] animate-pulse delay-150' : 'bg-stone-400'}`}></div>
        </div>
        <span className="text-[11px] font-bold uppercase tracking-widest text-stone-600">
          {status === 'connected' ? 'Kitchen Sync Active' : `Voice: ${status}`}
        </span>
      </div>

      {/* Manual Shortcuts Section */}
      <div className="w-full max-w-md mb-16">
        <h2 className="text-center text-[10px] font-bold uppercase tracking-[0.2em] text-stone-400 mb-6">
          Schnellzugriffe
        </h2>
        
        <div className="grid grid-cols-3 gap-4">
          {shortcuts.map((shortcut, index) => (
            <button key={index} className="flex flex-col items-center gap-3 p-4 rounded-2xl bg-[#F0F0EA]/50 hover:bg-[#F0F0EA] transition-all border border-stone-100">
              <div 
                className="w-14 h-14 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: shortcut.bgColor }}
              >
                {shortcut.icon}
              </div>
              <span className="text-xs font-bold leading-tight text-center">{shortcut.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Voice Interface */}
      <div className="flex-1 flex flex-col items-center justify-center w-full">
        <button 
          className="group relative"
          onClick={toggleVoice}
        >
          {/* Glow Effect */}
          <div className={`absolute inset-0 bg-[#5D4037] opacity-20 blur-3xl rounded-full transition-all duration-500 ${active ? 'scale-150 opacity-40' : 'scale-125'}`}></div>
          
          <div className={`relative w-48 h-48 bg-[#5D4037] rounded-full flex flex-col items-center justify-center text-white shadow-2xl transition-all duration-300 active:scale-95 p-4 ${active ? 'animate-pulse shadow-[0_0_50px_rgba(40,0,200,0.6)]' : ''}`}>
            {active ? <Mic size={40} className="mb-4" strokeWidth={2.5} /> : <MicOff size={40} className="mb-4" strokeWidth={2.5} />}
            <span className="text-sm font-bold uppercase tracking-wider">
              {active ? 'Zuhören...' : 'Starten'}
            </span>
          </div>
        </button>

        <p className="mt-12 italic text-stone-500 text-lg text-center max-w-[300px] min-h-[3rem] leading-relaxed">
          {transcript || '"Add 20 sourdough loaves to morning batch"'}
        </p>
      </div>
    </div>
  );
};

export default App;
