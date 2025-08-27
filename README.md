🤖 Bot de Senhas WiFi para Visitantes
Este projeto é um bot do Telegram, desenvolvido em Python, que automatiza a distribuição de senhas de acesso ao WiFi para visitantes. Ele usa um arquivo Excel como base de dados para gerenciar as senhas de forma segura e organizada.

✨ Funcionalidades em Destaque
Distribuição Automatizada: O bot entrega senhas únicas e pré-cadastradas para cada visitante.

Validação de Documentos: Suporta a validação de CPF, RG e passaporte, garantindo que a informação seja válida.

Controle de Uso: Uma senha, depois de entregue, é marcada e não pode ser reutilizada, e um limite de senhas é imposto por usuário.

Consulta Rápida: O visitante pode consultar facilmente as senhas que já recebeu.

⚙️ Como o Bot Funciona
Início: O visitante inicia a conversa com o comando /start.

Solicitação: O comando /wifi inicia o processo de pedido da senha.

Escolha do Dispositivo: O bot solicita o tipo de dispositivo (Celular ou Outro).

Documento: O visitante informa seu documento (CPF, RG ou Passaporte).

Entrega: O bot valida o documento, encontra uma senha disponível, preenche os dados no arquivo Excel e entrega a senha ao visitante.

Consulta: O comando /minhassenhas permite ao usuário ver as senhas que já foram cadastradas para seu ID.

📂 Estrutura do Projeto
biblioteca_visitante.py: O coração do projeto, com toda a lógica do bot.

config_bot_senhaBFF.py: Armazena o token do bot de forma segura.

password.xlsx: O banco de dados em Excel que contém as senhas. Importante: Deve ter as colunas nome, senha, documento, dispositivos, status e user_id.

requirements.txt: Lista todas as bibliotecas necessárias para rodar o projeto.

.gitignore: Arquivos e pastas que o Git deve ignorar (como o token do bot e o arquivo Excel).

🚀 Como Instalar e Rodar
Clone o Repositório:

git clone https://github.com/Gvargas1968/Senhas-Visitantes-WiFi.git
cd Senhas-Visitantes-WiFi

Instale as Dependências:

pip install -r requirements.txt

Configure o Token:

Crie o arquivo config_bot_senhaBFF.py.

Adicione a linha TELEGRAM_TOKEN = "<SEU_TOKEN>" e substitua <SEU_TOKEN> pelo seu token real.

Prepare a Base de Dados:

Crie o arquivo Excel password.xlsx e adicione as colunas necessárias.

Preencha as colunas nome e senha com os dados do seu WiFi, deixando as outras em branco.

Execute o Bot:

python biblioteca_visitante.py

Seu bot estará online e pronto para uso!
