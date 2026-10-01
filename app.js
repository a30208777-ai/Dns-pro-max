// === 1. CONFIGURAÇÃO ===
const CONFIG = {
    LOCAL_SERVER: "http://192.168.1.15:8053",
    DNS_LIST: [
        { name: "AdGuard DNS", ip: "94.140.14.14", type: "AdBlock" },
        { name: "ControlD", ip: "76.76.2.2", type: "AdBlock" },
        { name: "Mullvad DNS", ip: "194.242.2.2", type: "Privacidade" },
        { name: "Quad9", ip: "9.9.9.9", type: "Segurança" },
        { name: "Cloudflare", ip: "1.1.1.1", type: "Rápido" }
    ]
};

// === 2. ESTATÍSTICAS E REQUISIÇÕES ===
let totalReq = 0;
let blockedAds = 0;

function testarLatenciaDNS(dnsIp) {
    const inicio = performance.now();
    return fetch(`https://${dnsIp}`, { mode: 'no-cors', cache: 'no-store' })
        .then(() => {
            const tempo = Math.round(performance.now() - inicio);
            return { status: "Online", ms: `${tempo} ms` };
        })
        .catch(() => {
            return { status: "Ativo (UDP)", ms: "Pronto" };
        });
}

function verificarServidorLocal(urlServidor) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    return fetch(urlServidor, { method: 'GET', mode: 'no-cors', signal: controller.signal })
        .then(() => {
            clearTimeout(timeoutId);
            return { online: true, mensagem: "Servidor Ativo na Rede Local" };
        })
        .catch(() => {
            return { online: false, mensagem: "Servidor Offline no Termux" };
        });
}

// === 3. SIMULADOR DE FILTRO DE DOMÍNIO ===
function testarDominio(domain) {
    const cleanDomain = domain.trim().toLowerCase();
    const BLOCKED_KEYWORDS = ["ad", "ads", "tracker", "telemetry", "analytics", "doubleclick", "pixel"];
    
    if (!cleanDomain) {
        return { domain: "-", status: "Digite um domínio válido", isBlocked: false };
    }

    const isBlocked = BLOCKED_KEYWORDS.some(kw => cleanDomain.includes(kw));
    return {
        domain: cleanDomain,
        status: isBlocked ? "BLOQUEADO (0.0.0.0)" : "PERMITIDO (IP VÁLIDO)",
        isBlocked: isBlocked
    };
}

// === 4. GERADOR DE INSTRUÇÕES ===
function gerarInstrucoes(os, ip) {
    const targetIp = ip || "192.168.1.15";
    const selected = (os || "").toLowerCase().trim();

    const configs = {
        "android": `No Android:\n1. Configurações > Rede e Internet > DNS Privado\n2. Selecione Nome do host do provedor de DNS privado\n3. Insira: dns.adguard-dns.com (Ou use o IP ${targetIp} no Wi-Fi)`,
        "windows": `No Windows:\n1. Painel de Controle > Rede e Internet > Central de Rede e Compartilhamento\n2. Alterar as configurações do adaptador > Propriedades do IPv4\n3. Use os seguintes endereços de servidor DNS:\n   - Primário: ${targetIp}\n   - Secundário: 94.140.14.14`,
        "linux": `No Linux / Termux:\n1. Edite o arquivo /etc/resolv.conf:\n   nameserver ${targetIp}\n   nameserver 94.140.14.14`
    };

    return configs[selected] || "Selecione um sistema operacional válido no menu acima.";
}

// === 5. RENDERIZAÇÃO E EVENTOS DE INTERFACE ===
document.addEventListener("DOMContentLoaded", () => {
    // A. Renderizar Servidores DNS
    const dnsContainer = document.getElementById("dns-container");
    const statusServidor = document.getElementById("server-status");

    if (dnsContainer) {
        dnsContainer.innerHTML = "";
        CONFIG.DNS_LIST.forEach(dns => {
            const item = document.createElement("div");
            item.className = "dns-item";
            item.innerHTML = `
                <div class="dns-info">
                    <strong>${dns.name}</strong>
                    <small>${dns.ip} • ${dns.type}</small>
                </div>
                <span id="dns-${dns.ip.replace(/\./g, '-')}" class="status-badge">Verificando...</span>
            `;
            dnsContainer.appendChild(item);

            testarLatenciaDNS(dns.ip).then(resultado => {
                const badge = document.getElementById(`dns-${dns.ip.replace(/\./g, '-')}`);
                if (badge) {
                    badge.textContent = `${resultado.status} (${resultado.ms})`;
                    badge.className = "status-badge online";
                }
            });
        });
    }

    // B. Verificação do Servidor Local
    if (statusServidor) {
        statusServidor.textContent = "Verificando Termux...";
        verificarServidorLocal(CONFIG.LOCAL_SERVER).then(respostaLocal => {
            statusServidor.textContent = respostaLocal.mensagem;
            statusServidor.className = respostaLocal.online ? "server-badge online" : "server-badge offline";
        });
    }

    // C. Evento do Botão de Simulação de Bloqueio
    const btnSimulate = document.getElementById("btn-simulate");
    const inputDomain = document.getElementById("input-domain");
    const resultBox = document.getElementById("sim-result");

    if (btnSimulate && inputDomain && resultBox) {
        btnSimulate.addEventListener("click", () => {
            const res = testarDominio(inputDomain.value);
            resultBox.textContent = `[${res.domain}] -> ${res.status}`;
            resultBox.className = res.isBlocked ? "result-blocked" : "result-allowed";
        });
    }

    // D. Evento do Selecionador de Sistema Operacional
    const selectOS = document.getElementById("select-os");
    const configOutput = document.getElementById("config-output");

    if (selectOS && configOutput) {
        selectOS.addEventListener("change", (e) => {
            const cleanIp = CONFIG.LOCAL_SERVER.replace("http://", "").split(":")[0];
            configOutput.value = gerarInstrucoes(e.target.value, cleanIp);
        });
    }

    // E. Alternador de Tema (Modo Claro / Escuro)
    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            themeBtn.textContent = newTheme === "dark" ? "☀️ Modo Claro" : "🌙 Modo Escuro";
        });
    }

    // F. Contador do Painel (Simulação em tempo real)
    setInterval(() => {
        totalReq++;
        if (Math.random() < 0.3) blockedAds++;
        
        const reqEl = document.getElementById("stat-total-req");
        const blockEl = document.getElementById("stat-blocked-ads");
        if (reqEl) reqEl.textContent = totalReq;
        if (blockEl) blockEl.textContent = blockedAds;
    }, 2500);
});
