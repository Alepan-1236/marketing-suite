import streamlit as st
import json
import urllib.parse
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# Impostazioni della pagina
st.set_page_config(page_title="AI Marketing & Ads Suite", page_icon="🚀", layout="wide")

st.title("🚀 AI Marketing & Ads Suite")
st.markdown("Inserisci il brief della tua campagna: il sistema genererà strategia, post LinkedIn, carosello Meta con immagini, script TikTok e annunci Google Ads con conteggio caratteri.")

# Barra laterale per la chiave API
with st.sidebar:
    st.header("⚙️ Impostazioni")
    api_key = st.text_input("Inserisci la tua Gemini API Key:", type="password")
    st.markdown("[Recupera la tua chiave gratuita su Google AI Studio](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.info("💡 La chiave viene utilizzata solo per la sessione corrente e non viene salvata.")

# Schema Pydantic rigido
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
Sei un Senior Performance Marketer e Direttore Creativo multicanale.
REGOLE CRITICHE ASSOLUTE:
1. GOOGLE ADS: 'titoli_max_30_caratteri' max 30 caratteri (spazi inclusi). 'titoli_lunghi_max_90_caratteri' e 'descrizioni_max_90_caratteri' max 90 caratteri.
2. IMMAGINI: I prompt visivi devono essere descrittivi, fotorealistici o grafici, rigorosamente in INGLESE e privi di testi incorporati.
3. Rispetta rigorosamente lo schema JSON richiesto.
"""

def crea_url_immagine(prompt: str, width: int = 1080, height: int = 1080) -> str:
    prompt_codificato = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{prompt_codificato}?width={width}&height={height}&model=flux&nologo=true"

# Casella di inserimento del brief
brief_input = st.text_area(
    "Descrivi la campagna o il prodotto da promuovere:",
    placeholder="Es. Servizio di consulenza per aiutare le PMI ad adeguarsi alla NIS2 evitando sanzioni...",
    height=120
)

if st.button("✨ Genera Campagna Completa", type="primary"):
    if not api_key:
        st.error("Inserisci prima la tua Gemini API Key nella barra laterale a sinistra.")
    elif not brief_input.strip():
        st.warning("Inserisci una descrizione per la campagna prima di avviare.")
    else:
        with st.spinner("Elaborazione della strategia e generazione degli asset multicanale..."):
            try:
                client = genai.Client(api_key=api_key)
                
                # Lista di modelli con fallback automatico contro errori di traffico (503/404)
                modelli_candidati = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
                risposta = None
                ultimo_errore = None

                for mod in modelli_candidati:
                    try:
                        risposta = client.models.generate_content(
                            model=mod,
                            contents=f"Brief della campagna:\n\n{brief_input}",
                            config=types.GenerateContentConfig(
                                system_instruction=PROMPT_SISTEMA,
                                response_mime_type="application/json",
                                response_schema=PacchettoCampagnaCompleta,
                                temperature=0.2
                            )
                        )
                        if risposta and risposta.text:
                            break
                    except Exception as e:
                        ultimo_errore = e
                        continue

                if not risposta or not risposta.text:
                    raise ultimo_errore

                dati = json.loads(risposta.text)

                tab_strat, tab_li, tab_meta, tab_tt, tab_gads = st.tabs([
                    "🎯 Strategia", "💼 LinkedIn", "📸 Meta (IG & FB)", "🎵 TikTok & Reels", "🔍 Google Ads"
                ])

                with tab_strat:
                    st.subheader("Assetto Strategico")
                    st.write(f"**Angolo Chiave:** {dati['strategia']['idea_chiave']}")
                    st.write(f"**Target Principale:** {dati['strategia']['target']}")
                    st.write(f"**Tono di Voce:** {dati['strategia']['tono_voce']}")

                with tab_li:
                    st.subheader("Post per LinkedIn")
                    st.info(f"**Hook Iniziale:** {dati['linkedin']['gancio_iniziale']}")
                    st.text_area("Testo del Post:", dati['linkedin']['testo_post'], height=180)
                    st.write(f"**Chiamata all'azione:** {dati['linkedin']['cta_finale']}")
                    st.write("**Hashtags:** " + " ".join([f"#{h}" if not h.startswith('#') else h for h in dati['linkedin']['hashtag']]))
                    st.markdown("#### Immagine suggerita")
                    url_img_li = crea_url_immagine(dati['linkedin']['prompt_immagine_in_inglese'], 1200, 627)
                    st.image(url_img_li, caption="Grafica orizzontale per LinkedIn")

                with tab_meta:
                    st.subheader("Instagram & Facebook")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Caption Instagram:**")
                        st.text_area("Instagram Copy", dati['meta_instagram_facebook']['copy_instagram'], height=150)
                    with col2:
                        st.markdown("**Copy Facebook:**")
                        st.text_area("Facebook Copy", dati['meta_instagram_facebook']['copy_facebook'], height=150)

                    st.markdown("#### Slide per Carosello")
                    slides = dati['meta_instagram_facebook']['carosello_slide']
                    col_slides = st.columns(min(len(slides), 4))
                    for i, s in enumerate(slides):
                        with col_slides[i % 4]:
                            st.markdown(f"**Slide {s['numero']}:** {s['titolo_slide']}")
                            st.caption(s['testo_slide'])
                            url_slide = crea_url_immagine(s['prompt_grafica_inglese'], 800, 800)
                            st.image(url_slide)

                with tab_tt:
                    st.subheader("Sceneggiatura TikTok & Reels")
                    st.warning(f"**Hook (Primi 3 secondi):** {dati['tiktok_reels']['gancio_primi_3_secondi']}")
                    st.write(f"**Stile Audio:** {dati['tiktok_reels']['audio_consigliato']}")
                    st.markdown("#### Dettaglio Scene:")
                    for sc in dati['tiktok_reels']['scene_video']:
                        st.markdown(f"⏱️ **{sc['secondi']}**")
                        st.write(f"🎬 *Visivo:* {sc['cosa_mostrare']}")
                        st.write(f"🎙️ *Voce/Testo:* {sc['cosa_dire_o_scrivere']}")
                        st.divider()

                with tab_gads:
                    st.subheader("Campagna Google Ads (Search & PMax)")
                    st.markdown("##### Titoli Brevi (Limite 30 caratteri)")
                    for t in dati['google_ads']['titoli_max_30_caratteri']:
                        col_t1, col_t2 = st.columns([4, 1])
                        col_t1.code(t, language="text")
                        lunghezza = len(t)
                        col_t2.markdown(f"✅ `{lunghezza}/30`" if lunghezza <= 30 else f"❌ `{lunghezza}/30`")

                    st.markdown("##### Titoli Lunghi (Limite 90 caratteri)")
                    for tl in dati['google_ads']['titoli_lunghi_max_90_caratteri']:
                        st.code(f"{tl} ({len(tl)}/90)", language="text")

                    st.markdown("##### Descrizioni (Limite 90 caratteri)")
                    for d in dati['google_ads']['descrizioni_max_90_caratteri']:
                        st.code(f"{d} ({len(d)}/90)", language="text")

            except Exception as e:
                st.error(f"Si è verificato un errore durante la chiamata: {e}")
