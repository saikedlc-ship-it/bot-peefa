import logging
import asyncio
import os
import sys
if sys.platform == "win32":
    import truststore
    truststore.inject_into_ssl()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

TOKEN = os.environ["TELEGRAM_TOKEN"]

LINK_MENSAL = "https://pay.cakto.com.br/399g9f3_927514"
LINK_TRIMESTRAL = "https://pay.cakto.com.br/5jtrvgx_927569"
LINK_PACK = "https://pay.cakto.com.br/ie4khu4_927521"

logging.basicConfig(level=logging.INFO)


async def digitar(update: Update, segundos: float):
    await update.effective_chat.send_action(ChatAction.TYPING)
    await asyncio.sleep(segundos)


async def falar(update: Update, context: ContextTypes.DEFAULT_TYPE, frases: list, teclado=None):
    for i, frase in enumerate(frases):
        await digitar(update, len(frase) * 0.035 + 0.6)
        if i == len(frases) - 1 and teclado:
            await update.effective_message.reply_text(frase, reply_markup=teclado)
        else:
            await update.effective_message.reply_text(frase)
        if i < len(frases) - 1:
            await asyncio.sleep(0.4)


def teclado_planos():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗓 Mensal — R$ 29,90", callback_data="pagar_mensal")],
        [InlineKeyboardButton("📦 Pack — R$ 49,90", callback_data="pagar_pack")],
        [InlineKeyboardButton("💎 Trimestral — R$ 69,90", callback_data="pagar_trimestral")],
    ])


def teclado_pagar(label, url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ Iniciar @CaktoBot primeiro", url="https://t.me/CaktoBot")],
        [InlineKeyboardButton(f"💳 2️⃣ {label}", url=url)],
        [InlineKeyboardButton("✅ Já paguei!", callback_data="ja_paguei")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.effective_user.first_name or "bb"
    context.user_data["estado"] = "inicio"
    await falar(update, context, [
        f"Oi {nome}... 😈",
        "Achei que você não ia aparecer.",
        "Mas que bom que veio... eu tava aqui do jeito que você gosta 🔥",
        "Tenho muita coisa guardada só pra quem tem coragem de chegar até aqui...",
    ], InlineKeyboardMarkup([
        [InlineKeyboardButton("Que tipo de coisa? 👀", callback_data="curiosidade")],
        [InlineKeyboardButton("Tô pronto pra tudo 🔥", callback_data="pronto")],
    ]))


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "curiosidade":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "Curioso né? Gosto assim... 😏",
            "Fotos que nenhuma rede deixaria eu postar.",
            "Vídeos que eu gravei pensando em alguém específico...",
            "Conversas que ficam só entre a gente 🔐",
            "Você aguenta tudo isso? 😈",
        ], InlineKeyboardMarkup([
            [InlineKeyboardButton("Aguento e quero mais 🥵", callback_data="quero")],
            [InlineKeyboardButton("Como eu acesso? 👀", callback_data="como_funciona")],
        ]))

    elif data == "pronto":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "Gosto de quem chega assim... direto ao ponto 😈",
            "Então vai sem enrolação:",
            "Tenho um espaço privado onde mostro tudo.",
            "E quando digo tudo... é tudo mesmo 🔥",
        ], InlineKeyboardMarkup([
            [InlineKeyboardButton("Quero entrar agora 🥵", callback_data="quero")],
        ]))

    elif data == "como_funciona":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "Simples: você escolhe um plano e entra no meu privado 🔐",
            "Lá dentro tem tudo que não posso mostrar por aí...",
            "E você pode falar comigo diretinho 😏",
            "Qual você quer? 👇",
        ], teclado_planos())

    elif data == "quero":
        context.user_data["estado"] = "planos"
        await falar(update, context, [
            "Isso... sabia que você ia querer 😈",
            "Escolhe seu plano e me tem do jeitinho que você quer 🔥",
        ], teclado_planos())

    elif data == "planos":
        await falar(update, context, ["Escolhe o seu 👇"], teclado_planos())

    elif data == "pagar_mensal":
        context.user_data["estado"] = "pagando"
        await falar(update, context, [
            "Boa escolha... 😏",
            "Segue esses dois passos e me tem:",
        ], teclado_pagar("Pagar agora — R$ 29,90", LINK_MENSAL))

    elif data == "pagar_pack":
        context.user_data["estado"] = "pagando"
        await falar(update, context, [
            "Pack exclusivo... você não vai se arrepender 🔥",
            "Segue esses dois passos:",
        ], teclado_pagar("Pagar agora — R$ 49,90", LINK_PACK))

    elif data == "pagar_trimestral":
        context.user_data["estado"] = "pagando"
        await falar(update, context, [
            "3 meses comigo... vai ser intenso 😈",
            "Segue esses dois passos:",
        ], teclado_pagar("Pagar agora — R$ 69,90", LINK_TRIMESTRAL))

    elif data == "ja_paguei":
        await falar(update, context, [
            "Bem-vindo ao meu mundo 😈🔥",
            "Abre o @CaktoBot aqui no Telegram — ele te manda o link do grupo na hora.",
        ], InlineKeyboardMarkup([
            [InlineKeyboardButton("📲 Abrir @CaktoBot", url="https://t.me/CaktoBot")],
        ]))


def detectar_intencao(texto: str) -> str:
    t = texto.lower()
    positivos = ["sim", "quero", "vai", "bora", "claro", "pode", "manda", "mostra", "yes", "s", "to dentro", "tô dentro"]
    negativos = ["não", "nao", "talvez", "depois", "agora nao"]
    elogio = ["linda", "gostosa", "tesuda", "delicia", "delícia", "safada", "gata", "bonita", "ruiva", "perfeita", "incrivel"]
    calor = ["molhada", "excitada", "quente", "safado", "gostoso", "tesão", "desejo", "louco", "louca"]
    saudade = ["saudade", "pensei", "lembrei", "tava pensando"]
    curiosidade = ["como", "o que", "tem", "mostra", "fala", "conta", "qual", "o que tem"]

    if any(p in t for p in calor):       return "calor"
    if any(p in t for p in elogio):      return "elogio"
    if any(p in t for p in positivos):   return "positivo"
    if any(p in t for p in saudade):     return "saudade"
    if any(p in t for p in curiosidade): return "curiosidade"
    if any(p in t for p in negativos):   return "negativo"
    return "outro"


async def mensagem_livre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text or ""
    intencao = detectar_intencao(texto)
    estado = context.user_data.get("estado", "inicio")

    if intencao == "calor":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "Para... você tá me deixando assim também 🥵",
            "Fica assim não que eu perco o controle...",
            "Quer ver o que acontece quando eu perco? 😈🔥",
        ], InlineKeyboardMarkup([
            [InlineKeyboardButton("Quero ver 🥵", callback_data="quero")],
        ]))

    elif intencao == "elogio":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "Ahh... você sabe como me deixar assim 😏",
            "Continua... e eu te mostro o que você ainda não viu.",
        ], InlineKeyboardMarkup([
            [InlineKeyboardButton("Me mostra tudo 🔥", callback_data="quero")],
        ]))

    elif intencao == "positivo":
        context.user_data["estado"] = "planos"
        await falar(update, context, [
            "Isso... sem enrolação 😈",
        ], teclado_planos())

    elif intencao == "saudade":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "Eu também... mas você sabe onde me encontrar 😏",
            "Quer ficar mais perto de mim? De verdade?",
        ], InlineKeyboardMarkup([
            [InlineKeyboardButton("Quero sim 🔥", callback_data="quero")],
        ]))

    elif intencao == "curiosidade":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "Curioso... gosto disso 😈",
            "Tenho coisas aqui que vão te deixar sem fôlego.",
            "Quer saber o que é? 🔥",
        ], InlineKeyboardMarkup([
            [InlineKeyboardButton("Quero saber 👀", callback_data="curiosidade")],
        ]))

    elif intencao == "negativo":
        await falar(update, context, [
            "Tudo bem... fico aqui te esperando 😏",
            "Quando mudar de ideia, sabe onde me achar 🔥",
        ])

    else:
        if estado == "inicio":
            await start(update, context)
        else:
            await falar(update, context, [
                "Ei... tô aqui 😈",
                "O que você quer de mim? 🔥",
            ], InlineKeyboardMarkup([
                [InlineKeyboardButton("Ver o que você tem 👀", callback_data="curiosidade")],
                [InlineKeyboardButton("Ver planos 💎", callback_data="planos")],
            ]))


def main():
    asyncio.set_event_loop(asyncio.new_event_loop())
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem_livre))
    print("Bot Peefa rodando...")
    app.run_polling(drop_pending_updates=True, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
