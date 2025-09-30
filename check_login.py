
import os
from dotenv import load_dotenv
from services.goodwe_client import GoodWeClient
from utils.logger import get_logger

# Configurar logger
logger = get_logger(__name__)

def test_goodwe_login():
    """
    Testa o login na API GoodWe SEMS e imprime o resultado.
    """
    # Carregar variáveis de ambiente do arquivo .env
    load_dotenv()
    logger.info("Variáveis de ambiente carregadas.")

    # Obter credenciais do ambiente
    account = os.getenv('SEMS_ACCOUNT')
    password = os.getenv('SEMS_PASSWORD')
    login_region = os.getenv('SEMS_LOGIN_REGION', 'us')

    if not account or not password:
        logger.error("As variáveis de ambiente SEMS_ACCOUNT e SEMS_PASSWORD não foram encontradas.")
        logger.error("Verifique se o seu arquivo .env está configurado corretamente com:")
        logger.error("SEMS_ACCOUNT=seu_email@exemplo.com")
        logger.error("SEMS_PASSWORD=sua_senha")
        return

    logger.info(f"Tentando login com a conta: {account} na região: {login_region}")

    # Instanciar o cliente
    client = GoodWeClient(region=login_region)

    # Tentar fazer o login
    token = client.crosslogin(account, password)

    # Verificar e imprimir o resultado
    if token:
        logger.info("✅ Sucesso! Login na API GoodWe realizado com êxito.")
        logger.info(f"Token recebido (início): {token[:15]}...")
    else:
        logger.error("❌ Falha! Não foi possível fazer login na API GoodWe.")
        logger.error("Verifique suas credenciais (SEMS_ACCOUNT, SEMS_PASSWORD) e a região de login (SEMS_LOGIN_REGION) no arquivo .env.")

if __name__ == "__main__":
    test_goodwe_login()
