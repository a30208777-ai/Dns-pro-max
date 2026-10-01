import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE
    import dns.resolver
except ImportError:
    print("[!] Instale as dependências: pip install dnslib dnspython")
    sys.exit(1)

UPSTREAM_SERVERS = ["1.1.1.1", "9.9.9.9", "94.140.14.14"]
BLOCKED_KEYWORDS = ["ad", "ads", "tracker", "telemetry", "analytics", "doubleclick", "pixel"]

def e_dominio_bloqueado(domain_str):
    clean_domain = domain_str.rstrip('.').lower()
    return any(kw in clean_domain for kw in BLOCKED_KEYWORDS)

def processar_pacote_dns(raw_data):
    try:
        request = DNSRecord.parse(raw_data)
        qname = str(request.q.qname).rstrip('.')
        qtype_num = request.q.qtype
        qtype_str = QTYPE[qtype_num]

        reply = DNSRecord(
            DNSHeader(id=request.header.id, qr=1, aa=1, ra=1),
            q=request.q
        )

        if e_dominio_bloqueado(qname):
            print(f"[BLOQUEADO] -> {qname}")
            if qtype_str == 'A':
                reply.add_answer(RR(qname, QTYPE.A, rdata=A("0.0.0.0"), ttl=60))
            return reply.pack()

        resolver = dns.resolver.Resolver()
        resolver.nameservers = UPSTREAM_SERVERS
        resolver.timeout = 2
        resolver.lifetime = 2

        try:
            answers = resolver.resolve(qname, qtype_str)
            for rdata in answers:
                if qtype_str == 'A':
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(str(rdata)), ttl=300))
        except Exception:
            pass

        return reply.pack()
    except Exception as err:
        print(f"[ERRO PACOTE] {err}")
        return None

class RenderDNSProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Resposta HTTP válida para o scanner do Render aprovar a porta imediatamente
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"Servidor DNS Proxy em Python Ativo no Render!")

    def do_POST(self):
        # Trata pacotes DNS reais enviados via DoH/RFC 8484
        content_length = int(self.headers.get('Content-Length', 0))
        raw_dns_query = self.rfile.read(content_length)

        response_bytes = processar_pacote_dns(raw_dns_query)

        if response_bytes:
            self.send_response(200)
            self.send_header('Content-Type', 'application/dns-message')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_bytes)
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        return  # Silencia os logs no terminal para economizar recursos

if __name__ == "__main__":
    # Captura a porta exata que o Render exige
    port = int(os.environ.get("PORT", 8053))
    print(f"[*] A iniciar Servidor DNS Proxy no endereço 0.0.0.0 na porta {port}...")

    server = HTTPServer(('0.0.0.0', port), RenderDNSProxyHandler)
    server.serve_forever()
    
