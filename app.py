import streamlit as st
import json
import urllib.parse
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# Impostazione pagina
st.set_page_config(page_title="AI Marketing Suite", page_icon="🚀", layout="wide")
st.title("🚀 AI Marketing & Ads Suite")
st.caption("Crea la tua campagna completa multicanale: copy, script video, grafiche e Google Ads.")

# Barra laterale per inserire la chiave API
with st.sidebar:
    st.header("⚙️ Configurazione")
    api_key = st.text_input("Inserisci la tua Gemini API Key:", type="password")
    st.markdown("[Prendi la chiave gratuita su Google AI Studio](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.info("La chiave API resta privata nella tua sessione e non viene salvata.")

# Schema rigido con Pydantic
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
1. GOOGLE ADS: 'titoli_max_30_caratteri' max 30 caratteri ciascuno (spazi inclusi). 'titoli_lunghi_max_90_caratteri' e 'descrizioni_max_90_caratteri' max 90 caratteri ciascuno.
2. IMMAGINI: I prompt visivi devono essere in INGLESE e privi di scritte artificiali all'interno.
3. Riempi rigorosamente tutti i campi dello schema JSON.
"""

def crea_url_immagine(prompt: str, width: int = 1080, height: int = 1080) -> str:
    prompt_encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{prompt_encoded}?width={width}&height={height}&model=flux&nologo=true"

# Casella per il brief dell'utente
brief = st.text_area("Descrivi l'obiettivo della campagna, il prodotto/servizio e il target:", height=130, 
                     placeholder="Es. Lancio di un'app per trovare compagni di padel del proprio livello...")

if st.button("✨ Genera Campagna Completa", type="primary"):
    if not api_key:
        st.error("⚠️ Inserisci la tua Gemini API Key nella barra laterale a sinistra per procedere!")
    elif not brief.strip():
        st.warning("⚠️ Scrivi una descrizione o un'idea per la campagna prima di generare!")
    else:
        with st.spinner("L'AI sta orchestrando testi, script e immagini per tutti i canali..."):
            try:
                client = genai.Client(api_key=api_key)
                risposta = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=f"Brief della campagna:\n\n{brief}",
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA,
                        response_mime_type="application/json",
                        response_schema=PacchettoCampagnaCompleta,
                        temperature=0.2
                    )
                )
                dati = json.loads(risposta.text)

                # Organizzazione dell'output a schede
                tab_strat, tab_li, tab_meta, tab_tt, tab_gads = st.tabs([
                    "🎯 Strategia", "💼 LinkedIn", "📸 Meta (IG & FB)", "🎵 TikTok & Reels", "🔍 Google Ads"
                ])

                with tab_strat:
                    st.subheader("Sintesi Strategica")
                    st.write(f"**Angolo Chiave:** {dati['strategia']['idea_chiave']}")
                    st.write(f"**Target Audience:** {dati['strategia']['target']}")
                    st.write(f"**Tone of Voice:** {dati['strategia']['tono_voce']}")

                with tab_li:
                    st.subheader("Post per LinkedIn")
                    st.markdown(f"**Gancio:** {dati['linkedin']['gancio_iniziale']}")
                    st.text_area("Testo Post:", dati['linkedin']['testo_post'], height=200)
                    st.write(f"**CTA:** {dati['linkedin']['cta_finale']}")
                    st.write("**Hashtags:** " + " ".join([f"#{h}" if not h.startswith('#') else h for h in dati['linkedin']['hashtag']]))
                    st.markdown("#### Immagine Consigliata")
                    img_url = crea_url_immagine(dati['linkedin']['prompt_immagine_in_inglese'], 1200, 627)
                    st.image(img_url, caption="Grafica generata per LinkedIn (1.91:1)")

                with tab_meta:
                    st.subheader("Instagram & Facebook")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Copy Instagram:**")
                        st.text_area("Caption IG", dati['meta_instagram_facebook']['copy_instagram'], height=150)
                    with col2:
                        st.markdown("**Copy Facebook:**")
                        st.text_area("Copy FB", dati['meta_instagram_facebook']['copy_facebook'], height=150)
                    
                    st.markdown("#### Slide del Carosello")
                    slides = dati['meta_instagram_facebook']['carosello_slide']
                    cols = st.columns(min(len(slides), 4))
                    for idx, slide in enumerate(slides):
                        with cols[idx % 4]:
                            st.caption(f"Slide {slide['numero']}: {slide['titolo_slide']}")
                            st.write(slide['testo_slide'])
                            slide_img = crea_url_immagine(slide['prompt_grafica_inglese'], 800, 800)
                            st.image(slide_img)

                with tab_tt:
                    st.subheader("Script Video Verticale (TikTok / Reels)")
                    st.info(f"**Gancio primi 3s:** {dati['tiktok_reels']['gancio_primi_3_secondi']}")
                    st.write(f"**Traccia Audio Consigliata:** {dati['tiktok_reels']['audio_consigliato']}")
                    st.markdown("#### Sceneggiatura:")
                    for scena in dati['tiktok_reels']['scene_video']:
                        st.markdown(f"**⏱️ {scena['secondi']}**")
                        st.write(f"👀 *Visivo:* {scena['cosa_mostrare']}")
                        st.write(f"🗣️ *Parlato/Testo:* {scena['cosa_dire_o_scrivere']}")
                        st.divider()

                with tab_gads:
                    st.subheader("Annunci Google Ads (Search & Performance Max)")
                    st.markdown("##### Titoli Brevi (Max 30 caratteri)")
                    for t in dati['google_ads']['titoli_max_30_caratteri']:
                        st.code(f"{t} ({len(t)} car.)", language="text")

                    st.markdown("##### Titoli Lunghi (Max 90 caratteri)")
                    for tl in dati['google_ads']['titoli_lunghi_max_90_caratteri']:
                        st.code(f"{tl} ({len(tl)} car.)", language="text")

                    st.markdown("##### Descrizioni (Max 90 caratteri)")
                    for d in dati['google_ads']['descrizioni_max_90_caratteri']:
                        st.code(f"{d} ({len(d)} car.)", language="text")

            except Exception as e:
                st.error(f"Si è verificato un errore: {e}")
