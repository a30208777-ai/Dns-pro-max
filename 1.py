import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

DNS_DATABASE = {
    "AdGuard DNS (AdBlock)": "94.140.14.14",
    "AdGuard Family": "94.140.14.15",
    "ControlD (AdBlock)": "76.76.2.2",
    "Mullvad DNS (Privacy/AdBlock)": "194.242.2.2",
    "Quad9 (Segurança/Malware)": "9.9.9.9",
    "Cloudflare": "1.1.1.1",
    "Cloudflare Security": "1.1.1.2",
    "Cloudflare Family": "1.1.1.3",
    "CleanBrowsing Security": "185.228.168.9",
    "CleanBrowsing Family": "185.228.168.168",
    "Cisco OpenDNS": "208.67.222.222",
    "Google Public DNS": "8.8.8.8",
    "DNS.WATCH": "84.200.69.80",
    "Alternate DNS": "76.76.19.19"
}

def forward_query(query_data, upstream_ip):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.sendto(query_data, (upstream_ip, 53))
        response, _ = sock.recvfrom(4096)
        sock.close()
        return response
    except Exception:
        return None

def resolve_multi_dns(query_data, upstream_list):
    with ThreadPoolExecutor(max_workers=len(upstream_list)) as executor:
        futures = [executor.submit(forward_query, query_data, ip) for ip in upstream_list]
        for future in as_completed(futures):
            res = future.result()
            if res:
                return res
    return None

def handle_client(server_sock, data, addr, active_upstreams):
    response = resolve_multi_dns(data, active_upstreams)
    if response:
        server_sock.sendto(response, addr)

def start_dns_server(host="0.0.0.0", initial_port=5353, active_upstreams=None):
    if not active_upstreams:
        active_upstreams = list(DNS_DATABASE.values())

    # Lista de portas para tentar caso a inicial esteja ocupada
    candidate_ports = [initial_port, 5354, 8053, 1053, 9053]
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bound_port = None

    for p in candidate_ports:
        try:
            server_sock.bind((host, p))
            bound_port = p
            break
        except OSError:
            continue

    if bound_port is None:
        print("[!] Erro: Nenhuma das portas de teste (5353, 5354, 8053, 1053) estava livre.")
        return

    print("\n" + "=" * 65)
    print(f"[*] SERVIDOR PROXY DNS MULTI-UPSTREAM ATIVO")
    print(f"[*] Escutando em: {host}:{bound_port}")
    print(f"[*] Total de servidores DNS em paralelo: {len(active_upstreams)}")
    print("=" * 65)
    print("[*] Aguardando requisições... (Pressione Ctrl+C para sair)\n")

    try:
        while True:
            data, addr = server_sock.recvfrom(4096)
            threading.Thread(
                target=handle_client,
                args=(server_sock, data, addr, active_upstreams),
                daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\n[*] Encerrando o servidor DNS...")
    finally:
        server_sock.close()

if __name__ == "__main__":
    print("--- CONFIGURAÇÃO DO SERVIDOR DNS MULTI-UPSTREAM ---")
    print("Digite 'todos' para usar TODOS os servidores DNS listados em paralelo.")
    print("Digite um IP específico para defini-lo como preferencial.")
    print("Deixe em branco (pressione Enter) para usar todos os DNS por padrão.\n")

    user_input = input("Escolha (todos / IP / Enter): ").strip().lower()

    all_ips = list(DNS_DATABASE.values())

    if user_input == "" or user_input == "todos":
        upstreams = all_ips
        print("\n[+] Modo 'TODOS' ativado: O proxy consultará todos os servidores em paralelo.")
    else:
        upstreams = [user_input] + [ip for ip in all_ips if ip != user_input]
        print(f"\n[+] IP preferencial definido: {user_input} (com fallback para os demais).")

    start_dns_server(host="0.0.0.0", initial_port=5353, active_upstreams=upstreams)
    
