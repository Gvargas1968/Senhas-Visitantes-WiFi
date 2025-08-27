# Importa as classes e funções necessárias para interagir com a API do Telegram e manipular dados.
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes, CallbackQueryHandler
)
# A biblioteca pandas é usada para ler e escrever no arquivo Excel.
import pandas as pd
# O módulo 're' (expressões regulares) é usado para a validação de documentos.
import re
# Importa o token do bot de um arquivo de configuração separado para segurança.
from config_bot_senhaBFF import TELEGRAM_TOKEN

# --- Validação dos documentos ---
# Funções para validar o formato e o dígito verificador dos documentos.

def validar_cpf(cpf: str) -> bool:
    """Valida um número de CPF."""
    # Remove todos os caracteres não numéricos.
    cpf = re.sub(r'\D', '', cpf)
    # Verifica se tem 11 dígitos e se não é uma sequência de números iguais.
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    # Itera para calcular e verificar os dois dígitos verificadores.
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i+1) - num) for num in range(0, i))
        digito = ((soma * 10) % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True

def validar_rg(rg: str) -> bool:
    """Valida um número de RG."""
    # Remove caracteres não numéricos e verifica o comprimento.
    rg = re.sub(r'\D', '', rg)
    # RGs podem ter de 7 a 9 dígitos, dependendo do estado.
    return 7 <= len(rg) <= 9

def validar_passaporte(passaporte: str) -> bool:
    """Valida um número de passaporte no formato '2 letras, 6 ou 7 números'."""
    # Usa expressão regular para verificar o padrão.
    return bool(re.match(r'^[A-Z]{2}[0-9]{6,7}$', passaporte, re.IGNORECASE))

def documento_valido(doc: str) -> bool:
    """Verifica se o documento é um CPF, RG ou passaporte válido."""
    return validar_cpf(doc) or validar_rg(doc) or validar_passaporte(doc)

# Estados da conversa do bot
ESCOLHER_DISPOSITIVO, INFORMAR_DOCUMENTO = range(2)
# Nome do arquivo da base de dados.
ARQUIVO_SENHAS = "password.xlsx"

# --- Handlers dos comandos e fluxos de conversa ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /start. Apresenta o bot ao usuário."""
    await update.message.reply_text(
        "👋 Olá! Use /wifi para solicitar uma senha de acesso ao WiFi. "
        "Você irá preencher apenas o documento, o restante será feito automaticamente.\n\n"
        "Use /MinhasSenhas para consultar as senhas já recebidas."
    )

async def iniciar_wifi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler que inicia a conversa de solicitação de senha."""
    try:
        # Tenta ler o arquivo Excel.
        df = pd.read_excel(ARQUIVO_SENHAS, dtype=str)
    except Exception as e:
        await update.message.reply_text("⚠️ Erro ao acessar a base de senhas. Tente novamente mais tarde.")
        # Finaliza a conversa se houver erro.
        return ConversationHandler.END

    # Encontra a primeira linha com 'documento' vazio para atribuir a senha.
    disponiveis = df[df['documento'].isnull() | (df['documento'] == "")]
    if disponiveis.empty:
        await update.message.reply_text("🚫 Todas as senhas já foram entregues. Aguarde o próximo lote.")
        return ConversationHandler.END

    # Armazena o índice da senha e o nome do WiFi nos dados do usuário para uso posterior.
    context.user_data['senha_index'] = disponiveis.index[0]
    context.user_data['nome_wifi'] = disponiveis.iloc[0]['nome']

    # Cria o teclado com botões inline para a escolha do dispositivo.
    keyboard = [
        [InlineKeyboardButton("Celular", callback_data="Celular")],
        [InlineKeyboardButton("Outros Dispositivos", callback_data="Outros Dispositivos")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Escolha o tipo de dispositivo que irá conectar:",
        reply_markup=reply_markup
    )
    # Retorna o estado ESCOLHER_DISPOSITIVO, movendo a conversa para o próximo passo.
    return ESCOLHER_DISPOSITIVO

async def escolher_dispositivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para a escolha do dispositivo via botão inline."""
    query = update.callback_query
    await query.answer()
    escolha = query.data
    context.user_data['dispositivos'] = escolha
    # Edita a mensagem para pedir o documento.
    await query.edit_message_text(
        "Informe seu número de documento (CPF, RG ou Passaporte):"
    )
    # Move a conversa para o estado INFORMAR_DOCUMENTO.
    return INFORMAR_DOCUMENTO

async def informar_documento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o usuário informar o documento."""
    documento = update.message.text.strip()
    user_id = str(update.effective_user.id)

    try:
        df = pd.read_excel(ARQUIVO_SENHAS, dtype=str)
    except Exception as e:
        await update.message.reply_text("⚠️ Erro ao acessar a base de senhas.")
        return ConversationHandler.END

    # Lógica para limitar a quantidade de senhas por user_id.
    ja_usou = df['user_id'].fillna('').astype(str).str.strip() == user_id
    if ja_usou.sum() >= 2:
        await update.message.reply_text(
            "🚫 Você já recebeu o limite de 2 senhas. Não é possível solicitar mais."
        )
        return ConversationHandler.END

    # Verifica a validade do documento.
    if not documento_valido(documento):
        await update.message.reply_text(
            "❌ Documento inválido. Por favor, informe um CPF, RG ou passaporte válido."
        )
        # Permanece no mesmo estado para que o usuário tente novamente.
        return INFORMAR_DOCUMENTO

    # Preenche a linha correspondente no DataFrame com os dados do usuário.
    usuario = update.effective_user.full_name or ""
    status = "entregue"
    dispositivos = context.user_data.get('dispositivos', '')
    i = context.user_data['senha_index']
    nome_wifi = context.user_data['nome_wifi']

    df.at[i, 'usuario'] = usuario
    df.at[i, 'documento'] = documento
    df.at[i, 'dispositivos'] = dispositivos
    df.at[i, 'status'] = status
    df.at[i, 'user_id'] = user_id

    senha_wifi = df.at[i, 'senha']

    try:
        # Salva as alterações no arquivo Excel.
        df.to_excel(ARQUIVO_SENHAS, index=False)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Erro ao salvar seu registro: {e}")
        return ConversationHandler.END

    # Envia a senha para o usuário.
    await update.message.reply_text(
        f"✅ Registro realizado!\n\n"
        f"Nome WiFi: {nome_wifi}\n"
        f"Sua senha: {senha_wifi}\n\n"
        "Esta senha é única e não será entregue novamente. Guarde com segurança!"
    )
    # Finaliza a conversa.
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /cancelar. Encerra a conversa."""
    await update.message.reply_text("❌ Operação cancelada.")
    return ConversationHandler.END

# --- Módulo de consulta de senhas já entregues ---
async def consultar_senhas_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /MinhasSenhas. Consulta as senhas do usuário."""
    user_id = str(update.effective_user.id)
    try:
        df = pd.read_excel(ARQUIVO_SENHAS, dtype=str)
    except Exception as e:
        await update.message.reply_text("⚠️ Erro ao acessar a base de senhas.")
        return

    # Filtra as senhas pelo user_id do Telegram.
    senhas_usuario = df[df['user_id'].fillna('').astype(str).str.strip() == user_id]

    if senhas_usuario.empty:
        await update.message.reply_text(
            "🔍 Você ainda não recebeu nenhuma senha cadastrada neste bot."
        )
        return

    # Formata a resposta com as senhas encontradas.
    resposta = "🔑 Suas senhas cadastradas:\n\n"
    for idx, row in senhas_usuario.iterrows():
        resposta += (
            f"• Nome WiFi: {row.get('nome', '-')}\n"
            f"  Senha: {row.get('senha', '-')}\n"
            f"  Dispositivo: {row.get('dispositivos', '-')}\n"
            f"  Status: {row.get('status', '-')}\n\n"
        )
    await update.message.reply_text(resposta.strip())

# --- Configuração do Bot ---
if __name__ == '__main__':
    # Cria a aplicação do bot com o token do Telegram.
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Cria o ConversationHandler, que gerencia o fluxo da conversa.
    conv_handler = ConversationHandler(
        # Define o ponto de entrada, que inicia a conversa.
        entry_points=[CommandHandler('wifi', iniciar_wifi)],
        # Define os estados da conversa e os handlers correspondentes.
        states={
            ESCOLHER_DISPOSITIVO: [CallbackQueryHandler(escolher_dispositivo)],
            INFORMAR_DOCUMENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, informar_documento)],
        },
        # Define os comandos que encerram a conversa em qualquer estado.
        fallbacks=[CommandHandler('cancelar', cancelar)],
        # O estado da conversa é mantido por chat.
        per_chat=True,
        # 'per_user=False' faz com que a conversa seja única para o chat inteiro,
        # o que pode levar a comportamentos inesperados se mais de uma pessoa
        # estiver usando o bot ao mesmo tempo no mesmo chat.
        per_user=False
    )

    # Adiciona os handlers ao aplicativo.
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('cancelar', cancelar))
    app.add_handler(CommandHandler('minhassenhas', consultar_senhas_usuario))

    print("🤖 Bot de senhas WiFi rodando... Use /wifi")
    # Inicia o bot, buscando por novas mensagens.
    app.run_polling()
