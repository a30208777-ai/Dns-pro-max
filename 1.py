import socket
import threading
import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# Importação da biblioteca DNS
try:
    import dns.resolver
    import dns.message
    import dns.rdatatype
except ImportError:
    print("[!] A biblioteca 'dnspython' não está instalada. Certifica-te de ter 'dnspython' no requirements.txt.")

# === SERVIDORES DNS UPSTREAM (FALLBACK) ===
UPSTREAM_DNS = [
    "94.140.14.14",  # AdGuard DNS
    "76.76.2.2",     # ControlD
    "1.1.1.1"        # Cloudflare
]

# === LISTA DE BLOQUEIO (ADS / TRACKERS) ===
BLOCKED_KEYWORDS = ["ad", "ads", "tracker", "telemetry", "analytics", "doubleclick", "pixel"]

def dominio_bloqueado(domain):
    domain_lower = domain.lower()
    return any(kw in domain_lower for kw in BLOCKED_KEYWORDS)

# === HANDLER COMPATÍVEL COM ANDROID (DoH / HTTPS / HEALTH CHECK) ===
class AndroidDNSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Validação de status do Render / Painel Web
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response_data = {
            "status": "online",
            "service": "DNS Private Server / Android 9+ Compatible",
            "mode": "AdBlock Enabled"
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_POST(self):
        # Suporte a DNS over HTTPS (DoH) usado por navegadores e sistemas modernos
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            dns_req = dns.message.from_wire(post_data)
            qname = str(dns_req.question[0].name).rstrip('.')

            if dominio_bloqueado(qname):
                # Responde com IP 0.0.0.0 (Bloqueado)
                reply = dns.message.make_response(dns_req)
                reply.set_rcode(dns.rcode.NOERROR)
                self._send_dns_response(reply.to_wire())
            else:
                # Encaminha consulta para o Upstream
                resolver = dns.resolver.Resolver()
                resolver.nameservers = UPSTREAM_DNS
                answer = resolver.resolve(qname, dns_req.question[0].rdtype)
                
                reply = dns.message.make_response(dns_req)
                for rdata in answer:
                    reply.answer.append(dns.rrset.from_text(qname, 300, dns.rdataclass.IN, dns_req.question[0].rdtype, str(rdata)))
                self._send_dns_response(reply.to_wire())

        except Exception as e:
            self.send_response(400)
            self.end_headers()

    def _send_dns_response(self, wire_data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/dns-message')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(wire_data)

    def log_message(self, format, *args):
        return  # Silencia logs HTTP repetitivos

def rodar_servidor_http(porta):
    server = HTTPServer(('0.0.0.0', porta), AndroidDNSHandler)
    print(f"[*] Servidor DNS (DoH/HTTPS) compatível com Android ativo na porta {porta}")
    server.serve_forever()

# === INICIALIZAÇÃO ===
if __name__ == "__main__":
    # Obtém a porta atribuída dinamicamente pelo Render
    port_env = int(os.environ.get("PORT", 8053))

    print("[*] A iniciar serviço DNS Bloqueador compatível com Android 9+...")
    
    # Inicia o servidor HTTP/HTTPS
    rodar_servidor_http(port_env)
    
