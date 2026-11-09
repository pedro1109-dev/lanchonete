"""Configuração portátil: execute uma vez na raiz, antes do Docker ou instalação local."""
from pathlib import Path
import secrets
root=Path(__file__).resolve().parent
path=root/'.env'
if path.exists():
    print('.env já existe. Nenhuma configuração foi sobrescrita.')
else:
    senha=secrets.token_urlsafe(16)
    texto=(root/'.env.example').read_text(encoding='utf-8').replace('SUBSTITUA_POR_UMA_CHAVE_ALEATORIA',secrets.token_urlsafe(50)).replace('POSTGRES_PASSWORD=SUBSTITUA_POR_UMA_SENHA','POSTGRES_PASSWORD='+secrets.token_urlsafe(24)).replace('ADMIN_PASSWORD=SUBSTITUA_POR_UMA_SENHA','ADMIN_PASSWORD='+senha)
    path.write_text(texto,encoding='utf-8')
    print('Configuração criada. Usuário de teste: admin')
    print('Senha de teste:',senha)
    print('Guarde a senha. Ela também está em ADMIN_PASSWORD no .env.')
