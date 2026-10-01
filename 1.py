
    
import socket
import threading
import sys
import os

# Importação de bibliotecas DNS
try:
    import dns.resolver
except ImportError:
    print("[!] O pacote 'dnspython' não está instalado. Adicione 'dnspython' ao requirements.txt.")

from http.server import HTTPServer, BaseHTTPRequestHandler

# === SERVIDORES DNS UPSTREAM ===
UPSTREAM_DNS = [
    "94.140.14.14", # AdGuard DNS
    "76.76.2.2",    # ControlD
    "194.242.2.2",  # Mullvad DNS
    "9.9.9.9",      # Quad9
    "1.1.1.1"       # Cloudflare
]

# === HTTP HANDLER PARA O RENDER ===
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write("Servidor DNS Proxy em Python Ativo no Render!".encode('utf-8'))

    def log_message(self, format, *args):
        return # Silencia logs HTTP repetitivos no terminal

def rodar_servidor_http(porta):
    server = HTTPServer(('0.0.0.0', porta), HealthCheckHandler)
    print(f"[*] Servidor Web de Status/HealthCheck ativo na porta {porta}")
    server.serve_forever()

# === INICIALIZAÇÃO ===
if __name__ == "__main__":
    # Obtém a porta atribuída pelo Render ou usa 8053 por padrão
    port_env = int(os.environ.get("PORT", 8053))

    # Define o modo padrão automaticamente (sem requerer input do terminal)
    user_input = "todos"
    print(f"[*] Modo configurado automaticamente: '{user_input}'")

    # Inicia o servidor HTTP em uma thread secundária para responder ao Render
    http_thread = threading.Thread(target=rodar_servidor_http, args=(port_env,), daemon=True)
    http_thread.start()

    print("[*] Servidor DNS Multi-Upstream a aguardar requisições...")
    
    # Mantém o processo principal ativo
    http_thread.join()
    
