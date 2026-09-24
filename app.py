import streamlit as st
import json
import io
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# Configurazione grafica della pagina
st.set_page_config(page_title="AI Marketing & Ads Suite", page_icon="🚀", layout="wide")

# Stile CSS per rifinire l'interfaccia
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 6px; padding: 8px 16px; }
    .card-preview { border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 AI Marketing & Ads Suite")
st.markdown("Generatore multicanale completo con layout card professionali, copy social, annunci Google Ads e asset visivi.")

with st.sidebar:
    st.header("⚙️ Impostazioni")
    api_key = st.text_input("Inserisci la tua Gemini API Key:", type="password")
    st.markdown("[Recupera la chiave gratuita su Google AI Studio](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.info("💡 Suggerimento: descrivi con precisione target, USP e tono per ottenere i risultati migliori.")

# Schema Pydantic
class Strategia(BaseModel):
    idea_chiave: str
    target: str
    tono_voce: str

class DeliverableLinkedIn(BaseModel):
    gancio_iniziale: str
    testo_post: str
    cta_finale: str
    hashtag: List[str]
    prompt_immagine_in_inglese: str

class SlideCarosello(BaseModel):
    numero: int
    badge_argomento: str
    titolo_slide: str
    testo_slide: str
    prompt_grafica_inglese: str

class DeliverableMeta(BaseModel):
    copy_instagram: str
    copy_facebook: str
    carosello_slide: List[SlideCarosello]

class ScenaVideo(BaseModel):
    secondi: str
    cosa_mostrare: str
    cosa_dire_o_scrivere: str

class DeliverableTikTok(BaseModel):
    gancio_primi_3_secondi: str
    audio_consigliato: str
    scene_video: List[ScenaVideo]

class DeliverableGoogleAds(BaseModel):
    titoli_max_30_caratteri: List[str]
    titoli_lunghi_max_90_caratteri: List[str]
    descrizioni_max_90_caratteri: List[str]

class PacchettoCampagnaCompleta(BaseModel):
    strategia: Strategia
    linkedin: DeliverableLinkedIn
    meta_instagram_facebook: DeliverableMeta
    tiktok_reels: DeliverableTikTok
    google_ads: DeliverableGoogleAds

PROMPT_SISTEMA = """
Sei un Senior Performance Marketer e un Art Director creativo di calibro internazionale.
Il tuo compito è trasformare il brief dell'utente in una campagna integrata eccellente.

LINEE GUIDA VISIVE RIGIDE (IMPORTANTE):
- VIETATO generare prompt banali come 'a generic smartphone', 'two businessmen shaking hands' o stock photo dozzinali.
- Per ogni prompt visivo ('prompt_immagine_in_inglese', 'prompt_grafica_inglese'), adotta un punto di vista da Art Director:
  * Stile: fotografia editoriale cinematografica o 3D rendering minimalista contemporaneo.
  * Inquadratura e luce: 'shot on 35mm lens, atmospheric volumetric lighting, dark moody aesthetic, subtle neon accents, shallow depth of field'.
  * Metafore visive: prediligi rappresentazioni simboliche e pulite (es. server room monolitiche, origami geometrici, vetro sagomato, architetture industriali moderne).
  * Sempre in INGLESE e rigorosamente SENZA scritte o testi all'interno dell'immagine.

LINEE GUIDA ADS:
- 'titoli_max_30_caratteri': massimo 30 caratteri (spazi inclusi).
- 'titoli_lunghi_max_90_caratteri' e 'descrizioni_max_90_caratteri': massimo 90 caratteri.
"""

def genera_card_grafica(numero_slide: int, badge: str, titolo: str, testo: str) -> Image.Image:
    """Crea una slide grafica professionale in formato quadrato (1080x1080)."""
    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#0F172A")  # Slate 900 elegante
    draw = ImageDraw.Draw(img)

    # Dettagli grafici: linea di accento superiore
    draw.rectangle([(0, 0), (w, 16)], fill="#3B82F6")  # Accent Blue

    # Header: Badge e Numero di slide
    draw.rounded_rectangle([(80, 80), (360, 140)], radius=12, fill="#1E293B", outline="#334155", width=2)
    draw.text((105, 96), badge.upper()[:22], fill="#93C5FD")
    draw.text((w - 220, 96), f"{numero_slide:02d} / 05", fill="#64748B")

    # Separatore
    draw.line([(80, 180), (w - 80, 180)], fill="#1E293B", width=2)

    # Titolo (con a capo manuale su base caratteri)
    parole_titolo = titolo.split()
    righe_titolo = []
    linea_corr = ""
    for p in parole_titolo:
        if len(linea_corr + " " + p) < 22:
            linea_corr += (" " if linea_corr else "") + p
        else:
            righe_titolo.append(linea_corr)
            linea_corr = p
    if linea_corr:
        righe_titolo.append(linea_corr)

    y_pos = 280
    for riga in righe_titolo:
        draw.text((80, y_pos), riga, fill="#F8FAFC")
        y_pos += 80

    # Testo descrittivo
    parole_testo = testo.split()
    righe_testo = []
    linea_corr = ""
    for p in parole_testo:
        if len(linea_corr + " " + p) < 36:
            linea_corr += (" " if linea_corr else "") + p
        else:
            righe_testo.append(linea_corr)
            linea_corr = p
    if linea_corr:
        righe_testo.append(linea_corr)

    y_pos += 40
    for riga in righe_testo:
        draw.text((80, y_pos), riga, fill="#94A3B8")
        y_pos += 52

    # Footer con call to action del brand
    draw.rounded_rectangle([(80, h - 160), (w - 80, h - 80)], radius=16, fill="#1E293B")
    draw.text((120, h - 130), "SCORRI PER CONTINUARE  →", fill="#60A5FA")

    return img

def ottieni_url_flux(prompt: str, seed: int = 42, ar_ratio: str = "1:1") -> str:
    prompt_arricchito = f"{prompt}, editorial photography, highly detailed, dramatic studio lighting, 8k resolution"
    encoded = urllib.parse.quote(prompt_arricchito)
    dim = "width=1200&height=628" if ar_ratio == "16:9" else "width=1024&height=1024"
    return f"https://image.pollinations.ai/prompt/{encoded}?{dim}&model=flux&seed={seed}&nologo=true"

# Interfaccia Utente
brief_input = st.text_area(
    "Descrivi la campagna o il prodotto da promuovere:",
    placeholder="Es. Servizio di consulenza strategica per adeguamento alla NIS2 per PMI...",
    height=120
)

if st.button("✨ Genera Campagna Completa", type="primary"):
    if not api_key:
        st.error("Inserisci prima la tua Gemini API Key nella barra laterale a sinistra.")
    elif not brief_input.strip():
        st.warning("Inserisci una descrizione per la campagna.")
    else:
        with st.spinner("L'AI sta orchestrando testi, ads e architettura visiva..."):
            client = genai.Client(api_key=api_key)
            modelli = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
            risposta = None
            ultimo_errore = None

            for mod in modelli:
                try:
                    risposta = client.models.generate_content(
                        model=mod,
                        contents=f"Brief campagna:\n\n{brief_input}",
                        config=types.GenerateContentConfig(
                            system_instruction=PROMPT_SISTEMA,
                            response_mime_type="application/json",
                            response_schema=PacchettoCampagnaCompleta
                        )
                    )
                    if risposta and risposta.text:
                        break
                except Exception as e:
                    ultimo_errore = e
                    continue

            if not risposta or not risposta.text:
                st.error(f"Errore durante l'elaborazione con il modello: {ultimo_errore}")
            else:
                dati = json.loads(risposta.text)
                st.session_state["dati_campagna"] = dati

if "dati_campagna" in st.session_state:
    dati = st.session_state["dati_campagna"]

    tab_strat, tab_li, tab_meta, tab_tt, tab_gads = st.tabs([
        "🎯 Strategia", "💼 LinkedIn", "📸 Meta (IG & FB)", "🎵 TikTok & Reels", "🔍 Google Ads"
    ])

    with tab_strat:
        st.subheader("Assetto Strategico")
        st.markdown(f"**Angolo Chiave:** {dati['strategia']['idea_chiave']}")
        st.markdown(f"**Target Principale:** {dati['strategia']['target']}")
        st.markdown(f"**Tono di Voce:** {dati['strategia']['tono_voce']}")

    with tab_li:
        st.subheader("Post per LinkedIn")
        st.info(f"**Hook Iniziale:** {dati['linkedin']['gancio_iniziale']}")
        st.text_area("Testo Post:", dati['linkedin']['testo_post'], height=180)
        st.write(f"**CTA:** {dati['linkedin']['cta_finale']}")
        st.write("**Hashtags:** " + " ".join([f"#{h}" if not h.startswith('#') else h for h in dati['linkedin']['hashtag']]))
        st.markdown("#### Visual Consigliato (Formato Orizzontale 1.91:1)")
        url_li = ottieni_url_flux(dati['linkedin']['prompt_immagine_in_inglese'], seed=10, ar_ratio="16:9")
        st.image(url_li, caption="Rendering Fotografico per Post/Banner LinkedIn")

    with tab_meta:
        st.subheader("Instagram & Facebook")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Caption Instagram:**")
            st.text_area("Copy IG", dati['meta_instagram_facebook']['copy_instagram'], height=140)
        with col2:
            st.markdown("**Copy Facebook:**")
            st.text_area("Copy FB", dati['meta_instagram_facebook']['copy_facebook'], height=140)

        st.markdown("---")
        st.subheader("Carosello Grafico Pronto da Pubblicare")
        st.caption("Slide impaginate automaticamente con tipografia e struttura a card ad alta leggibilità:")
        
        slides = dati['meta_instagram_facebook']['carosello_slide']
        cols = st.columns(min(len(slides), 4))
        for idx, s in enumerate(slides):
            with cols[idx % 4]:
                card_img = genera_card_grafica(
                    numero_slide=s['numero'],
                    badge=s.get('badge_argomento', 'INSIGHT'),
                    titolo=s['titolo_slide'],
                    testo=s['testo_slide']
                )
                st.image(card_img, caption=f"Slide {s['numero']}")
                
                buf = io.BytesIO()
                card_img.save(buf, format="PNG")
                st.download_button(
                    label=f"⬇️ Scarica Slide {s['numero']}",
                    data=buf.getvalue(),
                    file_name=f"slide_{s['numero']}.png",
                    mime="image/png",
                    key=f"btn_dl_{idx}"
                )

    with tab_tt:
        st.subheader("Sceneggiatura TikTok & Reels")
        st.warning(f"**Gancio Primi 3s:** {dati['tiktok_reels']['gancio_primi_3_secondi']}")
        st.write(f"**Audio Suggerito:** {dati['tiktok_reels']['audio_consigliato']}")
        st.markdown("#### Scene del Video:")
        for sc in dati['tiktok_reels']['scene_video']:
            st.markdown(f"⏱️ **{sc['secondi']}**")
            st.write(f"🎬 *Visivo:* {sc['cosa_mostrare']}")
            st.write(f"🎙️ *Voce/Testo:* {sc['cosa_dire_o_scrivere']}")
            st.divider()

    with tab_gads:
        st.subheader("Annunci Google Ads")
        st.markdown("##### Titoli Brevi (Limite 30 caratteri)")
        for t in dati['google_ads']['titoli_max_30_caratteri']:
            c1, c2 = st.columns([4, 1])
            c1.code(t, language="text")
            c2.markdown(f"✅ `{len(t)}/30`" if len(t) <= 30 else f"❌ `{len(t)}/30`")

        st.markdown("##### Titoli Lunghi (Limite 90 caratteri)")
        for tl in dati['google_ads']['titoli_lunghi_max_90_caratteri']:
            st.code(f"{tl} ({len(tl)}/90)", language="text")

        st.markdown("##### Descrizioni (Limite 90 caratteri)")
        for d in dati['google_ads']['descrizioni_max_90_caratteri']:
            st.code(f"{d} ({len(d)}/90)", language="text")
