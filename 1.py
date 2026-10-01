import socket
import sys
import threading
import os

try:
    from dnslib import DNSRecord, DNSHeader, RR, A, AAAA, QTYPE
    import dns.resolver
except ImportError:
    print("[!] Instale as dependências executando: pip install dnslib dnspython")
    sys.exit(1)

# === CONFIGURAÇÕES DO SERVIDOR DNS REAL ===
HOST = '0.0.0.0'
PORT = int(os.environ.get("PORT", 53))  # Usa a porta 53 por padrão para DNS real
UPSTREAM_SERVERS = ["1.1.1.1", "9.9.9.9", "94.140.14.14"]

# Lista de palavras-chave para bloqueio direto no DNS
BLOCKED_KEYWORDS = ["ad", "ads", "tracker", "telemetry", "analytics", "doubleclick", "pixel"]

def e_dominio_bloqueado(domain_str):
    clean_domain = domain_str.rstrip('.').lower()
    return any(kw in clean_domain for kw in BLOCKED_KEYWORDS)

def processar_pacote_dns(raw_data):
    """
    Processa a requisição DNS binária e gera um pacote DNS binário real de resposta.
    """
    try:
        request = DNSRecord.parse(raw_data)
        qname = str(request.q.qname).rstrip('.')
        qtype_num = request.q.qtype
        qtype_str = QTYPE[qtype_num]

        # Cria a estrutura de cabeçalho da resposta
        reply = DNSRecord(
            DNSHeader(id=request.header.id, qr=1, aa=1, ra=1),
            q=request.q
        )

        # 1. BLOQUEIO REAL: Retorna IP NULL (0.0.0.0) se o domínio for anúncio
        if e_dominio_bloqueado(qname):
            print(f"[BLOQUEADO] -> {qname}")
            if qtype_str == 'A':
                reply.add_answer(RR(qname, QTYPE.A, rdata=A("0.0.0.0"), ttl=60))
            return reply.pack()

        # 2. RESOLUÇÃO REAL: Consulta servidores DNS upstream oficiais
        resolver = dns.resolver.Resolver()
        resolver.nameservers = UPSTREAM_SERVERS
        resolver.timeout = 2
        resolver.lifetime = 2

        try:
            answers = resolver.resolve(qname, qtype_str)
            for rdata in answers:
                if qtype_str == 'A':
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(str(rdata)), ttl=300))
                elif qtype_str == 'AAAA':
                    reply.add_answer(RR(qname, QTYPE.AAAA, rdata=AAAA(str(rdata)), ttl=300))
            print(f"[RESOLVIDO] -> {qname} ({qtype_str})")
        except Exception as e:
            # Em caso de erro na consulta, retorna a resposta sem registros
            pass

        return reply.pack()

    except Exception as err:
        print(f"[ERRO PACOTE] Falha ao processar bytes: {err}")
        return None

def escutar_udp(sock):
    """
    Escuta requisições DNS padrão via UDP/53.
    """
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            if data:
                # Trata cada requisição em uma thread separada para alta performance
                threading.Thread(target=tratar_cliente_udp, args=(sock, data, addr), daemon=True).start()
        except Exception as e:
            print(f"[ERRO UDP] {e}")
            break

def tratar_cliente_udp(sock, data, addr):
    resposta_binaria = processar_pacote_dns(data)
    if resposta_binaria:
        sock.sendto(resposta_binaria, addr)

if __name__ == "__main__":
    print(f"[*] A iniciar Servidor DNS NATIVO em {HOST}:{PORT} (UDP)...")
    
    # Cria o socket UDP para tratar tráfego DNS padrão
    sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        sock_udp.bind((HOST, PORT))
        print(f"[+] Servidor DNS Ativo e a escutar requisições reais!")
        escutar_udp(sock_udp)
    except PermissionError:
        print(f"[!] ERRO: Para rodar na porta {PORT} localmente precisa de permissões de ROOT (sudo/su).")
    except Exception as e:
        print(f"[!] Erro ao iniciar o socket: {e}")
    finally:
        sock_udp.close()
        
