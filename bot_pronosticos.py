import math
import os

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# El token se lee de la variable de entorno de Windows
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise SystemExit("Falta la variable de entorno TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# ---------------------------------------------------------
# DATOS: Sporting Cristal vs Atlético Grau
# ---------------------------------------------------------
sc_ultimos_5 = [
    {'goles_f': 2, 'goles_c': 1, 'remates_tot': 14, 'remates_arco': 5, 'corners': 6, 'resultado': 'V'},
    {'goles_f': 5, 'goles_c': 0, 'remates_tot': 18, 'remates_arco': 8, 'corners': 8, 'resultado': 'V'},
    {'goles_f': 0, 'goles_c': 1, 'remates_tot': 11, 'remates_arco': 3, 'corners': 5, 'resultado': 'D'},
    {'goles_f': 1, 'goles_c': 3, 'remates_tot': 10, 'remates_arco': 4, 'corners': 4, 'resultado': 'D'},
    {'goles_f': 4, 'goles_c': 1, 'remates_tot': 16, 'remates_arco': 7, 'corners': 7, 'resultado': 'V'}
    
]

grau_ultimos_5 = [
    {'goles_f': 3, 'goles_c': 1, 'remates_tot': 15, 'remates_arco': 6, 'corners': 5, 'resultado': 'V'},
    {'goles_f': 2, 'goles_c': 4, 'remates_tot': 11, 'remates_arco': 4, 'corners': 4, 'resultado': 'D'},
    {'goles_f': 1, 'goles_c': 0, 'remates_tot': 10, 'remates_arco': 3, 'corners': 6, 'resultado': 'V'},
    {'goles_f': 3, 'goles_c': 1, 'remates_tot': 14, 'remates_arco': 5, 'corners': 4, 'resultado': 'V'},
    {'goles_f': 1, 'goles_c': 0, 'remates_tot': 13, 'remates_arco': 4, 'corners': 7, 'resultado': 'V'}
]

# ---------------------------------------------------------
# DATOS: Deportivo Garcilaso vs Universitario
# ---------------------------------------------------------
garcilaso_ultimos_5 = [
    {'goles_f': 0, 'goles_c': 1, 'remates_tot': 13, 'remates_arco': 7, 'corners': 6, 'resultado': 'D'},
    {'goles_f': 4, 'goles_c': 2, 'remates_tot': 30, 'remates_arco': 10, 'corners': 12, 'resultado': 'V'},
    {'goles_f': 1, 'goles_c': 0, 'remates_tot': 8,  'remates_arco': 6, 'corners': 2, 'resultado': 'V'},
    {'goles_f': 4, 'goles_c': 1, 'remates_tot': 17, 'remates_arco': 9, 'corners': 4, 'resultado': 'V'},
    {'goles_f': 0, 'goles_c': 0, 'remates_tot': 13, 'remates_arco': 0, 'corners': 1, 'resultado': 'E'}
]

u_ultimos_5 = [
    {'goles_f': 2, 'goles_c': 1, 'remates_tot': 9, 'remates_arco': 6, 'corners': 3, 'resultado': 'V'},
    {'goles_f': 2, 'goles_c': 2, 'remates_tot': 14, 'remates_arco': 5, 'corners': 7, 'resultado': 'E'},
    {'goles_f': 4, 'goles_c': 2, 'remates_tot': 22, 'remates_arco': 9, 'corners': 8, 'resultado': 'V'},
    {'goles_f': 3, 'goles_c': 0, 'remates_tot': 15, 'remates_arco': 6, 'corners': 3, 'resultado': 'V'},
    {'goles_f': 3, 'goles_c': 2, 'remates_tot': 8, 'remates_arco': 6, 'corners': 3, 'resultado': 'V'}
]

# Factores de localía y parámetros del modelo
FACTOR_LOCAL = 1.10
FACTOR_VISITA = 0.90
MAX_GOLES = 10


def calcular_promedios(equipo):
    n = len(equipo)
    return {
        'goles_f': sum(p['goles_f'] for p in equipo) / n,
        'goles_c': sum(p['goles_c'] for p in equipo) / n,
        'corners': sum(p['corners'] for p in equipo) / n,
        'remates_tot': sum(p['remates_tot'] for p in equipo) / n,
        'remates_arco': sum(p['remates_arco'] for p in equipo) / n,
        'victorias': sum(1 for p in equipo if p['resultado'] == 'V'),
        'empates': sum(1 for p in equipo if p['resultado'] == 'E'),
        'derrotas': sum(1 for p in equipo if p['resultado'] == 'D'),
    }


def poisson(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def calcular_modelo(local, visita):
    lam_local = ((local['goles_f'] + visita['goles_c']) / 2) * FACTOR_LOCAL
    lam_visita = ((visita['goles_f'] + local['goles_c']) / 2) * FACTOR_VISITA

    p_local = p_empate = p_visita = 0.0
    for i in range(MAX_GOLES + 1):
        p_i = poisson(i, lam_local)
        for j in range(MAX_GOLES + 1):
            p = p_i * poisson(j, lam_visita)
            if i > j:
                p_local += p
            elif i == j:
                p_empate += p
            else:
                p_visita += p

    total = p_local + p_empate + p_visita
    lam_total = lam_local + lam_visita

    return {
        'lam_local': lam_local,
        'lam_visita': lam_visita,
        'lam_total': lam_total,
        'p_local': p_local / total * 100,
        'p_empate': p_empate / total * 100,
        'p_visita': p_visita / total * 100,
        'mas_1_5': (1 - math.exp(-lam_total) * (1 + lam_total)) * 100,
        'mas_2_5': (1 - math.exp(-lam_total) * (1 + lam_total + lam_total ** 2 / 2)) * 100,
        'ambos_anotan': (1 - math.exp(-lam_local)) * (1 - math.exp(-lam_visita)) * 100,
    }


@bot.message_handler(commands=['start'])
def enviar_menu(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("SC vs Grau", callback_data="partido_sc_grau"))
    markup.add(InlineKeyboardButton("Garcilaso vs Universitario", callback_data="partido_garci_u"))

    with open("portadallanos.png", "rb") as foto:
        bot.send_photo(
            chat_id=message.chat.id,
            photo=foto,
            caption="⚽ ¡Hola! Bienvenido a *Predicciones Llanos*.\n\nSelecciona el partido que deseas analizar:",
            reply_markup=markup,
            parse_mode="Markdown"
        )


@bot.callback_query_handler(func=lambda call: True)
def responder_boton(call):
    bot.answer_callback_query(call.id)

    if call.data == "partido_sc_grau":
        sc = calcular_promedios(sc_ultimos_5)
        grau = calcular_promedios(grau_ultimos_5)
        m = calcular_modelo(sc, grau)

        mensaje = (
            "📊 *ESTADÍSTICAS: SC vs GRAU*\n\n"
            f"⚽ Goles esperados: SC {m['lam_local']:.2f} - {m['lam_visita']:.2f} Grau (total {m['lam_total']:.2f})\n"
            f"🔥 +1.5 goles: {m['mas_1_5']:.0f}%\n"
            f"🔥 +2.5 goles: {m['mas_2_5']:.0f}%\n"
            f"🥅 Ambos anotan: {m['ambos_anotan']:.0f}%\n\n"
            "📈 *DESGLOSE PROMEDIO (últimos 5 partidos):*\n"
            "🔹 *Sporting Cristal*:\n"
            f"   • Córners: {sc['corners']:.1f} | Rem. totales: {sc['remates_tot']:.1f} | Al arco: {sc['remates_arco']:.1f}\n"
            f"   • Goles a favor: {sc['goles_f']:.1f} | En contra: {sc['goles_c']:.1f}\n"
            f"   • Racha: {sc['victorias']}V {sc['empates']}E {sc['derrotas']}D\n\n"
            "🔸 *Atlético Grau*:\n"
            f"   • Córners: {grau['corners']:.1f} | Rem. totales: {grau['remates_tot']:.1f} | Al arco: {grau['remates_arco']:.1f}\n"
            f"   • Goles a favor: {grau['goles_f']:.1f} | En contra: {grau['goles_c']:.1f}\n"
            f"   • Racha: {grau['victorias']}V {grau['empates']}E {grau['derrotas']}D\n\n"
            "⚖️ *PROBABILIDADES DE RESULTADO (suman 100%):*\n"
            f"🟢 Victoria Sporting Cristal: {m['p_local']:.0f}%\n"
            f"⚪ Empate: {m['p_empate']:.0f}%\n"
            f"🔴 Victoria Atlético Grau: {m['p_visita']:.0f}%"
        )
        
        with open("portada1.png", "rb") as foto:
            bot.send_photo(
                chat_id=call.message.chat.id,
                photo=foto,
                caption=mensaje,
                parse_mode="Markdown"
            )

    elif call.data == "partido_garci_u":
        garci = calcular_promedios(garcilaso_ultimos_5)
        uni = calcular_promedios(u_ultimos_5)
        m = calcular_modelo(garci, uni)

        mensaje = (
            "📊 *ESTADÍSTICAS: GARCILASO vs UNIVERSITARIO*\n\n"
            f"⚽ Goles esperados: Garcilaso {m['lam_local']:.2f} - {m['lam_visita']:.2f} Universitario (total {m['lam_total']:.2f})\n"
            f"🔥 +1.5 goles: {m['mas_1_5']:.0f}%\n"
            f"🔥 +2.5 goles: {m['mas_2_5']:.0f}%\n"
            f"🥅 Ambos anotan: {m['ambos_anotan']:.0f}%\n\n"
            "📈 *DESGLOSE PROMEDIO (últimos 5 partidos):*\n"
            "🔹 *Deportivo Garcilaso*:\n"
            f"   • Córners: {garci['corners']:.1f} | Rem. totales: {garci['remates_tot']:.1f} | Al arco: {garci['remates_arco']:.1f}\n"
            f"   • Goles a favor: {garci['goles_f']:.1f} | En contra: {garci['goles_c']:.1f}\n"
            f"   • Racha: {garci['victorias']}V {garci['empates']}E {garci['derrotas']}D\n\n"
            "🔸 *Universitario*:\n"
            f"   • Córners: {uni['corners']:.1f} | Rem. totales: {uni['remates_tot']:.1f} | Al arco: {uni['remates_arco']:.1f}\n"
            f"   • Goles a favor: {uni['goles_f']:.1f} | En contra: {uni['goles_c']:.1f}\n"
            f"   • Racha: {uni['victorias']}V {uni['empates']}E {uni['derrotas']}D\n\n"
            "⚖️ *PROBABILIDADES DE RESULTADO (suman 100%):*\n"
            f"🟢 Victoria Garcilaso: {m['p_local']:.0f}%\n"
            f"⚪ Empate: {m['p_empate']:.0f}%\n"
            f"🔴 Victoria Universitario: {m['p_visita']:.0f}%"
        )
        
        with open("portada2.png", "rb") as foto:
            bot.send_photo(
                chat_id=call.message.chat.id,
                photo=foto,
                caption=mensaje,
                parse_mode="Markdown"
            )


if __name__ == "__main__":
    print("El bot está funcionando. Ve a Telegram y envíale /start")
    bot.infinity_polling()
