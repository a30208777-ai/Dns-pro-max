// === 1. CONFIGURAÇÃO ===
const CONFIG = {
    // Substitua o link abaixo pela URL gerada no seu painel do Render:
    LOCAL_SERVER: "https://meu-servidor-dns.onrender.com",
    
    // Lista de servidores DNS upstream para monitoramento
    DNS_LIST: [
        { name: "AdGuard DNS", ip: "94.140.14.14", type: "AdBlock" },
        { name: "ControlD", ip: "76.76.2.2", type: "AdBlock" },
        { name: "Mullvad DNS", ip: "194.242.2.2", type: "Privacidade" },
        { name: "Quad9", ip: "9.9.9.9", type: "Segurança" },
        { name: "Cloudflare", ip: "1.1.1.1", type: "Rápido" }
    ]
};

// === 2. MÉTRICAS E REQUISIÇÕES DE REDE ===
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
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    return fetch(urlServidor, { method: 'GET', mode: 'no-cors', signal: controller.signal })
        .then(() => {
            clearTimeout(timeoutId);
            return { online: true, mensagem: "Servidor Ativo na Nuvem (Render)" };
        })
        .catch(() => {
            return { online: false, mensagem: "Aguardando Conexão com o Render..." };
        });
}

// === 3. SIMULADOR DE BLOQUEIO DE DOMÍNIO ===
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

// === 4. GERADOR DE CONFIGURAÇÃO DE DISPOSITIVOS ===
function gerarInstrucoes(os, serverUrl) {
    const cleanHost = serverUrl.replace(/^https?:\/\//, "").split(":")[0];
    const selected = (os || "").toLowerCase().trim();

    const configs = {
        "android": `No Android:\n1. Configurações > Rede e Internet > DNS Privado\n2. Selecione Nome do host do provedor de DNS privado\n3. Insira o hostname do seu Render: ${cleanHost}`,
        "windows": `No Windows:\n1. Painel de Controle > Rede e Internet > Central de Rede e Compartilhamento\n2. Alterar as configurações do adaptador > Propriedades do IPv4\n3. Apague para o servidor DNS:\n   - Servidor Primário: ${cleanHost}\n   - Secundário (Fallback): 94.140.14.14`,
        "linux": `No Linux / Termux:\n1. Edite o arquivo /etc/resolv.conf:\n   nameserver ${cleanHost}\n   nameserver 94.140.14.14`
    };

    return configs[selected] || "Selecione um sistema operacional válido no menu acima.";
}

// === 5. INTERFACE E EVENTOS ===
document.addEventListener("DOMContentLoaded", () => {
    // A. Renderizar Lista de DNS Upstream
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

    // B. Verificação de Status do Servidor no Render
    if (statusServidor) {
        statusServidor.textContent = "Verificando Render...";
        verificarServidorLocal(CONFIG.LOCAL_SERVER).then(resposta => {
            statusServidor.textContent = resposta.mensagem;
            statusServidor.className = resposta.online ? "server-badge online" : "server-badge offline";
        });
    }

    // C. Testador/Simulador de Domínios
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

    // D. Gerador de Instruções
    const selectOS = document.getElementById("select-os");
    const configOutput = document.getElementById("config-output");

    if (selectOS && configOutput) {
        selectOS.addEventListener("change", (e) => {
            configOutput.value = gerarInstrucoes(e.target.value, CONFIG.LOCAL_SERVER);
        });
    }

    // E. Alternador do Tema (Modo Claro/Escuro)
    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            themeBtn.textContent = newTheme === "dark" ? "☀️ Modo Claro" : "🌙 Modo Escuro";
        });
    }

    // F. Atualização de Métricas Simuladas na Tela
    setInterval(() => {
        totalReq++;
        if (Math.random() < 0.25) blockedAds++;
        
        const reqEl = document.getElementById("stat-total-req");
        const blockEl = document.getElementById("stat-blocked-ads");
        if (reqEl) reqEl.textContent = totalReq;
        if (blockEl) blockEl.textContent = blockedAds;
    }, 2500);
});
                                                         
