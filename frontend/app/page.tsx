"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { 
  MessagesSquare, 
  CalendarClock, 
  ShoppingBag, 
  LineChart, 
  Megaphone, 
  Database,
  ArrowRight,
  UploadCloud,
  Cpu,
  TrendingUp,
  BrainCircuit,
  Bot,
  Layers,
  ChevronRight,
  ShieldCheck,
  Zap,
  Globe,
  Server,
  Code
} from "lucide-react";

export default function LandingPage() {
  const [isVisible, setIsVisible] = useState<Record<string, boolean>>({});
  const [expandedFeature, setExpandedFeature] = useState<string | null>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible((prev) => ({ ...prev, [entry.target.id]: true }));
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );

    const elements = document.querySelectorAll(".animate-on-scroll");
    elements.forEach((el) => observer.observe(el));

    return () => elements.forEach((el) => observer.unobserve(el));
  }, []);

  const getVisibilityClass = (id: string) => 
    isVisible[id] ? "visible" : "";

  return (
    <div className="min-h-screen bg-[#0a0a1a] text-white selection:bg-purple-500/30 font-sans overflow-x-hidden relative">
      <style dangerouslySetInnerHTML={{__html: `
        .text-gradient { 
          background: linear-gradient(to right, #6366f1, #a855f7, #06b6d4, #6366f1); 
          -webkit-background-clip: text; 
          -webkit-text-fill-color: transparent; 
          background-clip: text; 
          color: transparent; 
          background-size: 300% auto; 
          animation: shine 6s linear infinite; 
        }
        @keyframes shine { to { background-position: 300% center; } }
        
        .glass-card { 
          background: rgba(255, 255, 255, 0.02); 
          backdrop-filter: blur(16px); 
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(255, 255, 255, 0.05); 
          transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .glass-card:hover { 
          border-color: rgba(255, 255, 255, 0.15); 
          transform: translateY(-8px); 
          box-shadow: 0 20px 40px -15px rgba(0,0,0,0.6); 
          background: rgba(255, 255, 255, 0.04);
        }
        
        .blob { 
          position: absolute; 
          filter: blur(90px); 
          z-index: 0; 
          opacity: 0.4; 
          animation: float 15s ease-in-out infinite; 
          border-radius: 50%;
        }
        .blob-1 { top: -10%; left: -10%; width: 50vw; height: 50vw; background: #6366f1; animation-delay: 0s; }
        .blob-2 { bottom: -20%; right: -10%; width: 60vw; height: 60vw; background: #a855f7; animation-delay: -5s; }
        .blob-3 { top: 40%; left: 50%; width: 40vw; height: 40vw; background: #06b6d4; opacity: 0.2; transform: translate(-50%, -50%); animation-delay: -10s; }
        
        @keyframes float { 
          0%, 100% { transform: translate(0, 0) scale(1); } 
          33% { transform: translate(30px, -50px) scale(1.1); } 
          66% { transform: translate(-20px, 20px) scale(0.9); } 
        }
        
        .animate-on-scroll { 
          opacity: 0; 
          transform: translateY(40px); 
          transition: opacity 0.8s ease-out, transform 0.8s cubic-bezier(0.16, 1, 0.3, 1); 
        }
        .animate-on-scroll.visible { 
          opacity: 1; 
          transform: translateY(0); 
        }
        .delay-100 { transition-delay: 100ms; }
        .delay-200 { transition-delay: 200ms; }
        .delay-300 { transition-delay: 300ms; }
        .delay-400 { transition-delay: 400ms; }
        
        .bg-grid { 
          background-image: 
            linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), 
            linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px); 
          background-size: 50px 50px; 
          mask-image: radial-gradient(ellipse at center, black 40%, transparent 80%);
          -webkit-mask-image: radial-gradient(ellipse at center, black 40%, transparent 80%);
        }
        
        .floating-ui { animation: float-ui 8s ease-in-out infinite; }
        .floating-ui-reverse { animation: float-ui-reverse 9s ease-in-out infinite; }
        @keyframes float-ui { 
          0%, 100% { transform: translateY(0px) rotate(0deg); } 
          50% { transform: translateY(-20px) rotate(1deg); } 
        }
        @keyframes float-ui-reverse { 
          0%, 100% { transform: translateY(0px) rotate(0deg); } 
          50% { transform: translateY(15px) rotate(-1deg); } 
        }

        .glow-btn {
          position: relative;
        }
        .glow-btn::before {
          content: "";
          position: absolute;
          inset: -2px;
          background: linear-gradient(90deg, #6366f1, #a855f7, #06b6d4);
          border-radius: inherit;
          z-index: -1;
          opacity: 0;
          transition: opacity 0.3s;
          filter: blur(8px);
        }
        .glow-btn:hover::before {
          opacity: 1;
        }
      `}} />

      {/* Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>
        <div className="absolute inset-0 bg-grid z-0"></div>
      </div>

      {/* Navbar */}
      <nav className="relative z-50 flex items-center justify-between px-6 py-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <span className="font-display font-bold text-xl tracking-tight">BusinessOS AI</span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-300">
          <a href="#features" className="hover:text-white transition-colors">Özellikler</a>
          <a href="#how-it-works" className="hover:text-white transition-colors">Nasıl Çalışır</a>
          <a href="#technology" className="hover:text-white transition-colors">Teknoloji</a>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
            Giriş Yap
          </Link>
          <Link href="/register" className="glow-btn relative inline-flex items-center justify-center px-6 py-2.5 text-sm font-semibold text-white bg-white/10 border border-white/20 rounded-full hover:bg-white/20 transition-all">
            Ücretsiz Başlayın
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 flex flex-col items-center">
        
        {/* Hero Section */}
        <section className="w-full max-w-7xl mx-auto px-6 pt-20 pb-32 flex flex-col lg:flex-row items-center gap-16 min-h-[90vh]">
          <div className="flex-1 flex flex-col items-start gap-8 z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs font-medium backdrop-blur-sm">
              <Zap className="w-3.5 h-3.5" />
              <span>Yapay Zekâ ile İşletme Yönetiminde Yeni Dönem</span>
            </div>
            
            <h1 className="font-display text-5xl lg:text-7xl font-bold leading-[1.1] tracking-tight">
              İşletmenizi <br />
              <span className="text-gradient">Yapay Zekâ</span> ile <br />
              Geleceğe Taşıyın
            </h1>
            
            <p className="text-lg text-gray-400 max-w-xl leading-relaxed font-sans">
              BusinessOS AI; müşteri desteği, randevular, satış, finans ve pazarlama süreçlerinizi otomatize eden çok ajanlı akıllı asistan platformudur. İşinizi büyütürken operasyonel yükünüzü yapay zekâya bırakın.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto mt-4">
              <Link href="/register" className="w-full sm:w-auto relative group inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-bold text-white bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full overflow-hidden transition-transform hover:scale-105 active:scale-95 shadow-[0_0_40px_-10px_rgba(99,102,241,0.6)]">
                <span className="relative z-10">Hemen Başlayın</span>
                <ArrowRight className="w-5 h-5 relative z-10 group-hover:translate-x-1 transition-transform" />
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              </Link>
              
              <Link href="#features" className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium text-white bg-white/5 border border-white/10 rounded-full hover:bg-white/10 transition-colors backdrop-blur-md">
                Özellikleri Keşfedin
              </Link>
            </div>
          </div>

          <div className="flex-1 relative w-full max-w-lg lg:max-w-none aspect-square lg:aspect-auto h-[500px]">
            {/* Abstract UI Mockup */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative w-full max-w-md floating-ui">
                <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-2xl blur opacity-30"></div>
                <div className="relative bg-[#0f1423]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl">
                  {/* Mockup Header */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                        <TrendingUp className="w-5 h-5 text-indigo-400" />
                      </div>
                      <div>
                        <div className="h-2 w-24 bg-white/20 rounded-full mb-2"></div>
                        <div className="h-1.5 w-16 bg-white/10 rounded-full"></div>
                      </div>
                    </div>
                    <div className="flex gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-red-400/50"></div>
                      <div className="w-2.5 h-2.5 rounded-full bg-yellow-400/50"></div>
                      <div className="w-2.5 h-2.5 rounded-full bg-green-400/50"></div>
                    </div>
                  </div>
                  
                  {/* Mockup Body */}
                  <div className="space-y-4">
                    <div className="flex gap-4">
                      <div className="h-24 w-1/3 bg-white/5 rounded-xl border border-white/5 p-3 flex flex-col justify-end">
                         <div className="h-2 w-full bg-white/10 rounded-full mb-2"></div>
                         <div className="h-6 w-3/4 bg-green-400/20 rounded-md"></div>
                      </div>
                      <div className="h-24 w-2/3 bg-white/5 rounded-xl border border-white/5 p-3 flex items-end gap-2">
                        {[40, 70, 45, 90, 65, 80].map((h, i) => (
                          <div key={i} className="w-full bg-indigo-500/40 rounded-t-sm" style={{ height: `${h}%` }}></div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="bg-white/5 rounded-xl border border-white/5 p-4 space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-blue-400" />
                        </div>
                        <div className="h-2 w-32 bg-white/20 rounded-full"></div>
                      </div>
                      <div className="pl-11 space-y-2">
                        <div className="h-1.5 w-full bg-white/10 rounded-full"></div>
                        <div className="h-1.5 w-4/5 bg-white/10 rounded-full"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Decorative floating elements */}
              <div className="absolute top-10 -right-10 w-24 h-24 bg-purple-500/10 rounded-2xl border border-purple-500/20 backdrop-blur-xl floating-ui-reverse flex items-center justify-center shadow-xl">
                <MessagesSquare className="w-8 h-8 text-purple-400" />
              </div>
              <div className="absolute bottom-10 -left-10 w-20 h-20 bg-cyan-500/10 rounded-2xl border border-cyan-500/20 backdrop-blur-xl floating-ui flex items-center justify-center shadow-xl delay-200">
                <CalendarClock className="w-8 h-8 text-cyan-400" />
              </div>
            </div>
          </div>
        </section>

        {/* Features Section (Agents) */}
        <section id="features" className="w-full max-w-7xl mx-auto px-6 py-24">
          <div id="features-header" className={`flex flex-col items-center text-center mb-16 animate-on-scroll ${getVisibilityClass('features-header')}`}>
            <h2 className="font-display text-3xl md:text-5xl font-bold mb-4">6 Güçlü <span className="text-gradient">Yapay Zekâ Ajanı</span></h2>
            <p className="text-gray-400 max-w-2xl text-lg">İşletmenizin her departmanı için özel olarak eğitilmiş, RAG teknolojisi ile donatılmış sanal çalışanlarınızla tanışın.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                id: "feat-1",
                icon: <MessagesSquare className="w-6 h-6 text-[#4c6fff]" />,
                title: "Müşteri Destek",
                desc: "SSS ve dökümanlarınıza dayanarak müşteri sorularını 7/24 anında ve doğru yanıtlar.",
                color: "#4c6fff",
                details: [
                  "\"Çalışma saatleriniz nedir?\"",
                  "\"İade politikanız nasıl işliyor?\"",
                  "\"Fiyat listenizi görebilir miyim?\""
                ]
              },
              {
                id: "feat-2",
                icon: <CalendarClock className="w-6 h-6 text-[#f59e0b]" />,
                title: "Randevu Yönetim",
                desc: "Takviminizi senkronize eder, çakışmaları önler ve müşteriler için akıllı planlama yapar.",
                color: "#f59e0b",
                details: [
                  "Uygun saatleri otomatik bulur",
                  "Çakışan randevuları engeller",
                  "İptal/tamamlama durumunu takip eder"
                ]
              },
              {
                id: "feat-3",
                icon: <ShoppingBag className="w-6 h-6 text-[#10b981]" />,
                title: "Satış & Öneri",
                desc: "Müşteri davranışlarını analiz ederek kişiselleştirilmiş ürün/hizmet önerilerinde bulunur.",
                color: "#10b981",
                details: [
                  "\"Elimde ne var, hangisini önerirsin?\"",
                  "En az tercih edilen hizmeti tespit eder",
                  "Fiyat/süre karşılaştırması yapar"
                ]
              },
              {
                id: "feat-4",
                icon: <LineChart className="w-6 h-6 text-[#a855f7]" />,
                title: "Finansal Analiz",
                desc: "Gelir-gider tablolarınızı yorumlar, trendleri tespit eder ve büyüme fırsatlarını raporlar.",
                color: "#a855f7",
                details: [
                  "\"Bu ay kaç randevu tamamlandı?\"",
                  "\"En popüler hizmet hangisi?\"",
                  "Randevu durum dağılımını gösterir"
                ]
              },
              {
                id: "feat-5",
                icon: <Megaphone className="w-6 h-6 text-[#f43f5e]" />,
                title: "Pazarlama",
                desc: "Hedef kitlenize uygun yaratıcı kampanya fikirleri ve içerik stratejileri üretir.",
                color: "#f43f5e",
                details: [
                  "Az tercih edilen hizmet için promosyon önerir",
                  "Sosyal medya gönderi metni yazar",
                  "Müşteri sayısına göre kampanya ölçekler"
                ]
              },
              {
                id: "feat-6",
                icon: <Database className="w-6 h-6 text-[#06b6d4]" />,
                title: "RAG Bilgi Tabanı",
                desc: "Tüm dökümanlarınızı vektör veritabanında saklar, ajanların şirket kurallarını bilmesini sağlar.",
                color: "#06b6d4",
                details: [
                  "PDF, Word, TXT dosyaları destekler",
                  "Otomatik olarak parçalara ayırıp işler",
                  "Tüm ajanlar aynı bilgiyi paylaşır"
                ]
              }
            ].map((feature, i) => (
              <div 
                key={feature.id} 
                id={feature.id} 
                onClick={() => setExpandedFeature(expandedFeature === feature.id ? null : feature.id)}
                className={`glass-card rounded-2xl p-6 relative overflow-hidden group animate-on-scroll delay-${(i%3 + 1)*100} ${getVisibilityClass(feature.id)} cursor-pointer`}
              >
                <div 
                  className="absolute top-0 right-0 w-32 h-32 opacity-10 rounded-full blur-2xl transition-opacity group-hover:opacity-30" 
                  style={{ backgroundColor: feature.color, transform: "translate(30%, -30%)" }}
                ></div>
                <div 
                  className="w-12 h-12 rounded-xl mb-6 flex items-center justify-center border bg-white/5"
                  style={{ borderColor: `color-mix(in srgb, ${feature.color} 20%, transparent)` }}
                >
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold font-display mb-3">{feature.title} Ajanı</h3>
                <p className="text-gray-400 leading-relaxed text-sm">{feature.desc}</p>

                {expandedFeature === feature.id && (
                  <ul className="mt-4 flex flex-col gap-2 border-t border-white/10 pt-4">
                    {feature.details.map((d, idx) => (
                      <li key={idx} className="text-xs text-gray-400 flex items-start gap-2">
                        <span className="mt-1 h-1 w-1 rounded-full shrink-0" style={{ backgroundColor: feature.color }} />
                        {d}
                      </li>
                    ))}
                  </ul>
                )}

                <div className="mt-6 flex items-center text-sm font-medium transition-colors" style={{ color: feature.color }}>
                  <span>{expandedFeature === feature.id ? "Kapat" : "Detayları İncele"}</span>
                  <ChevronRight
                    className={`w-4 h-4 ml-1 transition-transform ${expandedFeature === feature.id ? "rotate-90" : "opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0"}`}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="w-full bg-white/[0.02] border-y border-white/5 py-24 relative">
          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div id="hw-header" className={`text-center mb-20 animate-on-scroll ${getVisibilityClass('hw-header')}`}>
              <h2 className="font-display text-3xl md:text-5xl font-bold mb-4">Nasıl Çalışır?</h2>
              <p className="text-gray-400 max-w-xl mx-auto">Sadece 3 adımda işletmenizi yapay zekâya entegre edin ve otomatik pilotta büyümeye başlayın.</p>
            </div>

            <div className="flex flex-col md:flex-row items-center justify-center gap-10 md:gap-4 lg:gap-10">
              {[
                {
                  id: "step-1",
                  icon: <UploadCloud className="w-8 h-8 text-indigo-400" />,
                  title: "1. Verilerinizi Yükleyin",
                  desc: "Şirket politikalarınızı, ürünlerinizi ve SSS dökümanlarınızı platforma yükleyin."
                },
                {
                  id: "step-2",
                  icon: <Cpu className="w-8 h-8 text-purple-400" />,
                  title: "2. Ajanları Aktifleştirin",
                  desc: "İhtiyacınız olan ajanları seçin ve RAG teknolojisi ile işletmenize özel eğitin."
                },
                {
                  id: "step-3",
                  icon: <TrendingUp className="w-8 h-8 text-cyan-400" />,
                  title: "3. İşletmenizi Büyütün",
                  desc: "Ajanlar arka planda çalışırken siz sadece raporları izleyin ve stratejiye odaklanın."
                }
              ].map((step, i, arr) => (
                <div key={step.id} className="flex flex-col md:flex-row items-center relative w-full md:w-1/3">
                  <div id={step.id} className={`flex flex-col items-center text-center relative z-10 w-full animate-on-scroll delay-${(i+1)*100} ${getVisibilityClass(step.id)}`}>
                    <div className="w-20 h-20 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-6 shadow-xl backdrop-blur-md relative group">
                      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                      {step.icon}
                    </div>
                    <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                    <p className="text-gray-400 text-sm leading-relaxed max-w-xs">{step.desc}</p>
                  </div>
                  {i < arr.length - 1 && (
                    <div className="hidden md:block absolute top-10 left-1/2 w-full h-[2px] bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-transparent -z-10 translate-x-[50%]"></div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Tech Stack / Architecture */}
        <section id="technology" className="w-full max-w-7xl mx-auto px-6 py-24">
          <div className="flex flex-col lg:flex-row items-center gap-16">
            <div id="tech-text" className={`flex-1 space-y-8 animate-on-scroll ${getVisibilityClass('tech-text')}`}>
              <div>
                <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">Güçlü ve Modern Mimari</h2>
                <p className="text-gray-400 text-lg">Platformumuz en son teknolojilerle inşa edilmiş, güvenli ve ölçeklenebilir bir altyapıya sahiptir.</p>
              </div>
              
              <div className="space-y-4">
                {[
                  { icon: <Layers className="w-5 h-5 text-indigo-400" />, title: "Multi-Agent Mimari", desc: "Birbirleriyle iletişim kurabilen bağımsız yapay zekâ birimleri." },
                  { icon: <BrainCircuit className="w-5 h-5 text-purple-400" />, title: "RAG (Retrieval-Augmented Generation)", desc: "Sadece size ait verilerle, halüsinasyon olmadan kesin cevaplar." },
                  { icon: <ShieldCheck className="w-5 h-5 text-cyan-400" />, title: "Multi-Tenant Yapı", desc: "Her işletme için izole edilmiş, güvenli veri depolama alanı." }
                ].map((item, i) => (
                  <div key={i} className="flex gap-4 items-start">
                    <div className="mt-1 w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
                      {item.icon}
                    </div>
                    <div>
                      <h4 className="font-bold text-lg">{item.title}</h4>
                      <p className="text-gray-400 text-sm">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div id="tech-visual" className={`flex-1 w-full animate-on-scroll delay-200 ${getVisibilityClass('tech-visual')}`}>
              <div className="glass-card rounded-2xl p-8 border border-white/10 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl"></div>
                
                <h3 className="font-mono text-sm text-gray-400 mb-6 flex items-center gap-2"><Code className="w-4 h-4"/> Tech Stack</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { name: "Next.js", type: "Frontend", bg: "bg-black" },
                    { name: "FastAPI", type: "Backend", bg: "bg-[#059669]/20" },
                    { name: "PostgreSQL", type: "Database", bg: "bg-[#336791]/20" },
                    { name: "pgvector", type: "Vector DB", bg: "bg-[#0284c7]/20" },
                    { name: "OpenAI", type: "LLM", bg: "bg-white/10" },
                    { name: "LangChain", type: "AI Orchestration", bg: "bg-green-500/20" }
                  ].map((tech, i) => (
                    <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col items-center justify-center gap-2 hover:bg-white/10 transition-colors">
                      <div className={`w-12 h-12 rounded-full ${tech.bg} flex items-center justify-center text-sm font-bold`}>
                        {tech.name.charAt(0)}
                      </div>
                      <div className="text-center">
                        <div className="font-bold text-sm">{tech.name}</div>
                        <div className="text-xs text-gray-500">{tech.type}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Stats / Social Proof */}
        <section className="w-full bg-gradient-to-b from-transparent to-[#12172a] border-t border-white/5 mt-10 pb-20">
          <div className="max-w-7xl mx-auto px-6 pt-20">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 divide-x divide-white/5">
              {[
                { val: "6+", label: "Yapay Zekâ Ajanı" },
                { val: "7/24", label: "Aktif Çalışma" },
                { val: "%100", label: "İzole Veri Yapısı" },
                { val: "RAG", label: "Mimarisi İle" }
              ].map((stat, i) => (
                <div key={i} id={`stat-${i}`} className={`flex flex-col items-center justify-center text-center px-4 animate-on-scroll delay-${(i+1)*100} ${getVisibilityClass(`stat-${i}`)}`}>
                  <div className="text-4xl md:text-5xl font-display font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 mb-2">
                    {stat.val}
                  </div>
                  <div className="text-sm text-gray-400 font-medium uppercase tracking-wider">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full border-t border-white/10 bg-[#05050f] pt-16 pb-8">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
            <div className="space-y-4 lg:col-span-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <span className="font-display font-bold text-lg">BusinessOS AI</span>
              </div>
              <p className="text-gray-400 text-sm max-w-sm leading-relaxed">
                Modern işletmeler için geliştirilmiş, çok ajanlı yapay zekâ tabanlı yönetim platformu. Operasyonlarınızı otomatikleştirin ve büyümeye odaklanın.
              </p>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-white/5 border border-white/10 text-xs text-gray-400">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                Sistemler Aktif
              </div>
            </div>
            
            <div>
              <h4 className="font-bold mb-4">Platform</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><Link href="#features" className="hover:text-white transition-colors">Ajanlar</Link></li>
                <li><Link href="#how-it-works" className="hover:text-white transition-colors">Nasıl Çalışır</Link></li>
                <li><Link href="#technology" className="hover:text-white transition-colors">Teknoloji</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-bold mb-4">Hesap</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><Link href="/login" className="hover:text-white transition-colors">Giriş Yap</Link></li>
                <li><Link href="/register" className="hover:text-white transition-colors">Kayıt Ol</Link></li>
                <li><Link href="/dashboard" className="hover:text-white transition-colors">Panele Git</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="flex flex-col md:flex-row items-center justify-between pt-8 border-t border-white/10 text-xs text-gray-500">
            <p>© {new Date().getFullYear()} BusinessOS AI. Mezuniyet Projesi.</p>
            <div className="flex items-center gap-4 mt-4 md:mt-0">
              <div className="flex items-center gap-1"><Server className="w-3 h-3"/> V1.0.0</div>
              <div className="flex items-center gap-1"><Globe className="w-3 h-3"/> Türkçe</div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
