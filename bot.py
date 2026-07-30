import logging
import asyncio
import os
import sys
from collections import deque
if sys.platform == "win32":
    import truststore
    truststore.inject_into_ssl()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

TOKEN = os.environ["TELEGRAM_TOKEN"]
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://bot-peefa.onrender.com")

LINK_MENSAL = "https://pay.cakto.com.br/399g9f3_927514"
LINK_MENSAL_10 = f"{LINK_MENSAL}?coupon=peefa10"
LINK_MENSAL_25 = f"{LINK_MENSAL}?coupon=peefa25"
LINK_PACK = "https://pay.cakto.com.br/ie4khu4_927521"
LINK_CONTEUDO = "https://pay.cakto.com.br/3avwwk5_937172"
LINK_CHAMADA = "https://pay.cakto.com.br/99x5v2v_937182"
LINK_PERSONALIZADO = "https://pay.cakto.com.br/vgxhayb_937188"

DISCRICAO = "Pagamento 100% discreto — nada aparece na fatura, e no PIX é ainda mais rápido 💸"

TEASER_VIDEO_ID = os.environ.get("TEASER_VIDEO_ID")
TEASER_PHOTO_ID = os.environ.get("TEASER_PHOTO_ID")
REENG1_VIDEO_ID = os.environ.get("REENG1_VIDEO_ID")
REENG2_VIDEO_ID = os.environ.get("REENG2_VIDEO_ID")
PIX_TUTORIAL_ID = os.environ.get("PIX_TUTORIAL_ID")

CONVITE_PLANOS = [
    "sabia que você ia querer 😈",
    "lá dentro é: fotos e vídeos que não posto em nenhuma rede 🔥 conteúdo novo toda semana 🔥 e eu no seu direct, sem filtro 😏",
    "escolhe como você quer me ter 👇",
]

PASSOS_PAGAMENTO = "1️⃣ toca em pagar agora, escolhe Pix e finaliza\n2️⃣ volta aqui e aperta ✅ Já paguei!"

logging.basicConfig(level=logging.INFO)

_UPDATES_VISTOS_SET = set()
_UPDATES_VISTOS_ORDEM = deque()
_MAX_UPDATES_VISTOS = 1000


def ja_processado(update_id: int) -> bool:
    if update_id in _UPDATES_VISTOS_SET:
        return True
    _UPDATES_VISTOS_SET.add(update_id)
    _UPDATES_VISTOS_ORDEM.append(update_id)
    if len(_UPDATES_VISTOS_ORDEM) > _MAX_UPDATES_VISTOS:
        antigo = _UPDATES_VISTOS_ORDEM.popleft()
        _UPDATES_VISTOS_SET.discard(antigo)
    return False


async def digitar(update: Update, segundos: float):
    await update.effective_chat.send_action(ChatAction.TYPING)
    await asyncio.sleep(segundos)


async def enviar_teaser(update: Update):
    try:
        if TEASER_VIDEO_ID:
            await update.effective_chat.send_video(TEASER_VIDEO_ID, has_spoiler=True)
        elif TEASER_PHOTO_ID:
            await update.effective_chat.send_photo(TEASER_PHOTO_ID, has_spoiler=True)
    except Exception:
        logging.exception("Falha ao enviar teaser")


async def receber_midia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ja_processado(update.update_id):
        return
    msg = update.effective_message
    if msg.video:
        logging.info(f"FILE_ID_VIDEO={msg.video.file_id}")
        await msg.reply_text("peguei o file_id do vídeo, tá nos logs do Render 📋")
    elif msg.photo:
        logging.info(f"FILE_ID_PHOTO={msg.photo[-1].file_id}")
        await msg.reply_text("peguei o file_id da foto, tá nos logs do Render 📋")


def nome_lembrete(chat_id: int) -> str:
    return f"lembrete_{chat_id}"


def agendar_lembrete(context: ContextTypes.DEFAULT_TYPE, chat_id: int, label: str, url: str):
    if not context.job_queue:
        return
    nome = nome_lembrete(chat_id)
    for job in context.job_queue.get_jobs_by_name(nome):
        job.schedule_removal()
    context.job_queue.run_once(lembrar_pagamento, when=330, chat_id=chat_id, name=nome, data=("simples", label, url))


def agendar_lembrete_mensal(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    if not context.job_queue:
        return
    nome = nome_lembrete(chat_id)
    for job in context.job_queue.get_jobs_by_name(nome):
        job.schedule_removal()
    context.job_queue.run_once(lembrar_pagamento, when=330, chat_id=chat_id, name=nome, data=("mensal_estagio1",))


def cancelar_lembrete(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    if not context.job_queue:
        return
    for job in context.job_queue.get_jobs_by_name(nome_lembrete(chat_id)):
        job.schedule_removal()


async def lembrar_pagamento(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    user_data = context.application.user_data.get(chat_id, {})
    if user_data.get("estado") != "pagando":
        return
    tipo = context.job.data[0]

    if tipo == "simples":
        _, label, url = context.job.data
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(1.5)
        await context.bot.send_message(
            chat_id,
            "ainda tá aberto pra você... 😏 não vou deixar por muito mais tempo não 🔥",
            reply_markup=teclado_pagar(label, url),
        )
        return

    if tipo == "mensal_estagio1":
        if REENG1_VIDEO_ID:
            await context.bot.send_video(chat_id, REENG1_VIDEO_ID, has_spoiler=True)
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(1.5)
        await context.bot.send_message(
            chat_id,
            "🔥 oferta relâmpago... fiquei pensando em você e separei um desconto 😏 corre que não vou deixar por muito tempo",
            reply_markup=teclado_pagar("Pagar agora — 10% OFF", LINK_MENSAL_10),
        )
        context.job_queue.run_once(
            lembrar_pagamento, when=900, chat_id=chat_id, name=nome_lembrete(chat_id), data=("mensal_estagio2",)
        )

    elif tipo == "mensal_estagio2":
        if REENG2_VIDEO_ID:
            await context.bot.send_video(chat_id, REENG2_VIDEO_ID, has_spoiler=True)
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(1.5)
        await context.bot.send_message(
            chat_id,
            "🚨 última chance... nunca fiz isso por ninguém 😢 deixei 25% de desconto de brinde, sem desculpa dessa vez",
            reply_markup=teclado_pagar("Pagar agora — 25% OFF", LINK_MENSAL_25),
        )


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
        [InlineKeyboardButton("🔥 Grupo VIP · Hoje por R$ 17,90", callback_data="pagar_mensal")],
        [InlineKeyboardButton("📹 Chamada de Vídeo — R$ 89,90", callback_data="pagar_chamada")],
        [InlineKeyboardButton("🔥 Ver experiências exclusivas", callback_data="extras")],
    ])


def teclado_extras():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔞 Conteúdo Proibido — R$ 39,90", callback_data="pagar_conteudo")],
        [InlineKeyboardButton("📹 Chamada de Vídeo comigo — R$ 89,90", callback_data="pagar_chamada")],
        [InlineKeyboardButton("🎁 Faço o que você quiser — R$ 197,00", callback_data="pagar_personalizado")],
        [InlineKeyboardButton("« Ver planos do grupo", callback_data="planos")],
    ])


def teclado_pagar(label, url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💳 {label}", url=url)],
        [InlineKeyboardButton("✅ Já paguei!", callback_data="ja_paguei")],
    ])


async def enviar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE, intro: str, label: str, url: str):
    await falar(update, context, [intro])
    teclado = teclado_pagar(label, url)
    if PIX_TUTORIAL_ID:
        await digitar(update, 1.2)
        await update.effective_chat.send_photo(PIX_TUTORIAL_ID, caption=PASSOS_PAGAMENTO, reply_markup=teclado)
    else:
        await digitar(update, len(PASSOS_PAGAMENTO) * 0.035 + 0.6)
        await update.effective_message.reply_text(PASSOS_PAGAMENTO, reply_markup=teclado)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ja_processado(update.update_id):
        return
    nome = update.effective_user.first_name or "bb"
    logging.info(f"NOVO_START chat_id={update.effective_chat.id} nome={nome} username={update.effective_user.username}")
    context.user_data["estado"] = "aquecendo"
    await enviar_teaser(update)
    await falar(update, context, [
        f"Oi {nome}... 😈 achei que você não ia aparecer",
        "me fala uma coisa... o que você quer de mim? 👀",
    ])


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if ja_processado(update.update_id):
        return
    data = query.data

    if data == "curiosidade":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "curioso né? gosto assim... 😏 fotos que nenhuma rede deixaria eu postar, vídeos que gravei pensando em alguém específico. você aguenta? 😈",
        ])

    elif data == "pronto":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "gosto de quem chega assim... direto ao ponto 😈 tenho um espaço privado onde mostro tudo — e quando digo tudo, é tudo mesmo 🔥 quer entrar?",
        ])

    elif data == "como_funciona":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "simples: você escolhe um plano, entra no meu privado e tem acesso a tudo que não mostro em lugar nenhum 🔐 discreto, via Telegram. qual você quer? 👇",
        ], teclado_planos())

    elif data == "quero":
        context.user_data["estado"] = "planos"
        await falar(update, context, CONVITE_PLANOS, teclado_planos())

    elif data == "planos":
        await falar(update, context, [
            "escolhe como você quer me ter 👇",
        ], teclado_planos())

    elif data == "extras":
        context.user_data["estado"] = "extras"
        await falar(update, context, [
            "isso aqui é pra quem quer de verdade... 😈 escolhe o que você quer comigo:",
        ], teclado_extras())

    elif data == "pagar_conteudo":
        context.user_data["estado"] = "pagando"
        label, url = "Pagar agora — R$ 39,90", LINK_CONTEUDO
        agendar_lembrete(context, update.effective_chat.id, label, url)
        await enviar_pagamento(update, context, "conteúdo proibido... só pra você 🔞", label, url)

    elif data == "pagar_chamada":
        context.user_data["estado"] = "pagando"
        label, url = "Pagar agora — R$ 89,90", LINK_CHAMADA
        agendar_lembrete(context, update.effective_chat.id, label, url)
        await enviar_pagamento(update, context, "uma chamada só sua e minha... 📹😈", label, url)

    elif data == "pagar_personalizado":
        context.user_data["estado"] = "pagando"
        label, url = "Pagar agora — R$ 197,00", LINK_PERSONALIZADO
        agendar_lembrete(context, update.effective_chat.id, label, url)
        await enviar_pagamento(update, context, "faço o que você quiser... vídeo, foto, áudio — só pra você 🎁🔥", label, url)

    elif data == "pagar_mensal":
        context.user_data["estado"] = "pagando"
        label, url = "Pagar agora — R$ 17,90", LINK_MENSAL
        agendar_lembrete_mensal(context, update.effective_chat.id)
        await enviar_pagamento(update, context, "boa escolha... 😏 nesse horário ainda tá por R$ 17,90, com garantia de 7 dias 🔥", label, url)

    elif data == "pagar_pack":
        context.user_data["estado"] = "pagando"
        label, url = "Pagar agora — R$ 49,90", LINK_PACK
        agendar_lembrete(context, update.effective_chat.id, label, url)
        await enviar_pagamento(update, context, "pack exclusivo... você não vai se arrepender 🔥", label, url)

    elif data == "ja_paguei":
        cancelar_lembrete(context, update.effective_chat.id)
        await falar(update, context, [
            "perfeito 🔥 agora só um passo: abre o @CaktoBot aqui no Telegram e manda qualquer mensagem pra ele — é ele quem vai te mandar o link do grupo automaticamente 🔐",
        ], InlineKeyboardMarkup([
            [InlineKeyboardButton("📲 Abrir @CaktoBot agora", url="https://t.me/CaktoBot")],
        ]))


def detectar_intencao(texto: str) -> str:
    t = texto.lower()
    positivos = ["sim", "quero", "vai", "bora", "claro", "pode", "manda", "mostra", "yes", "to dentro", "tô dentro"]
    negativos = ["não", "nao", "talvez", "depois", "agora nao"]
    elogio = ["linda", "gostosa", "tesuda", "delicia", "delícia", "safada", "gata", "bonita", "ruiva", "perfeita", "incrivel"]
    calor = ["molhada", "excitada", "quente", "safado", "gostoso", "tesão", "desejo", "louco", "louca", "pelada", "nua", "nu", "sem roupa", "mostra tudo", "buceta", "pau", "rola", "sexo", "foder", "trepar", "gozar", "piroca", "ppk", "xoxota", "cuzão", "bundão", "peito", "seio", "calcinha", "fio dental"]
    saudade = ["saudade", "pensei", "lembrei", "tava pensando"]
    curiosidade = ["como", "o que", "o que tem", "me fala", "me conta", "qual é", "qual e"]
    duvida = ["dúvida", "duvida", "não entendi", "nao entendi", "como funciona", "como é", "como e", "me explica", "não sei", "nao sei", "é seguro", "e seguro", "é discreto", "e discreto", "é discreta", "e discreta", "discreto", "discreta", "funciona como", "como assim", "que grupo", "que conteudo", "que conteúdo"]

    if any(p in t for p in calor):       return "calor"
    if any(p in t for p in elogio):      return "elogio"
    if any(p in t for p in saudade):     return "saudade"
    if any(p in t for p in duvida):      return "duvida"
    if any(p in t for p in positivos):   return "positivo"
    if any(p in t for p in curiosidade): return "curiosidade"
    if any(p in t for p in negativos):   return "negativo"
    return "outro"


async def mensagem_livre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ja_processado(update.update_id):
        return
    texto = update.message.text or ""
    intencao = detectar_intencao(texto)
    estado = context.user_data.get("estado", "inicio")

    if intencao == "calor":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "para... você tá me deixando assim também 🥵 quer ver o que acontece quando eu perco o controle? 😈",
        ])

    elif intencao == "elogio":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "ahh você sabe como me deixar assim 😏 quer ver o que tenho escondido só pra você?",
        ])

    elif intencao == "positivo":
        context.user_data["estado"] = "planos"
        await falar(update, context, CONVITE_PLANOS, teclado_planos())

    elif intencao == "saudade":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "eu também... mas você sabe onde me encontrar 😏 quer ficar mais perto de mim de verdade?",
        ])

    elif intencao == "curiosidade":
        context.user_data["estado"] = "aquecendo"
        await falar(update, context, [
            "curioso... gosto disso 😈 tenho coisas aqui que vão te deixar sem fôlego. quer saber?",
        ])

    elif intencao == "duvida":
        if context.user_data.get("duvida_respondida"):
            context.user_data["estado"] = "planos"
            await falar(update, context, [
                "é exatamente isso 😏 escolhe um plano e a gente começa 👇",
            ], teclado_planos())
        else:
            context.user_data["duvida_respondida"] = True
            context.user_data["estado"] = "aquecendo"
            await falar(update, context, [
                "pode perguntar à vontade 😏 é simples — você escolhe um plano, entra no meu privado e eu mando tudo que não mostro em lugar nenhum 🔐 discreto, pelo Telegram. quer entrar?",
            ])

    elif intencao == "negativo":
        await falar(update, context, [
            "tudo bem... fico aqui te esperando 😏 quando mudar de ideia é só falar",
        ])

    else:
        if not context.user_data.get("estado"):
            await start(update, context)
        else:
            context.user_data["estado"] = "planos"
            await falar(update, context, CONVITE_PLANOS, teclado_planos())


def main():
    asyncio.set_event_loop(asyncio.new_event_loop())
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, receber_midia))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem_livre))
    porta = int(os.environ.get("PORT", 8080))
    print("Bot Peefa rodando (webhook)...")
    app.run_webhook(
        listen="0.0.0.0",
        port=porta,
        url_path=TOKEN,
        webhook_url=f"{RENDER_URL}/{TOKEN}",
        drop_pending_updates=False,
        allowed_updates=["message", "callback_query"],
    )


if __name__ == "__main__":
    main()
