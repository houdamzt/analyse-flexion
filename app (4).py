import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import math

# --- Constantes ---
BETA_CONFLIT = 10

# --- Fonctions complètes ---
def estimer_longueur_col_femoral(offset_mm, ccd_deg):
    ccd_rad = np.radians(ccd_deg)
    return offset_mm / np.sin(ccd_rad)

def vecteur_col_abduction(ccd_deg, tf_deg, delta_deg, gamma_deg, offset_mm):
    theta = np.pi - np.radians(ccd_deg + gamma_deg)
    delta = np.radians(delta_deg)
    tf = np.radians(tf_deg)
    long_col = estimer_longueur_col_femoral(offset_mm, ccd_deg)
    ux = np.sin(theta) * long_col
    uy = (-np.cos(delta) * np.cos(theta) * long_col) - (np.sin(delta) * np.sin(tf) * long_col)
    uz = (-np.sin(delta) * np.cos(theta) * long_col) + (np.cos(delta) * np.sin(tf) * long_col)
    return np.array([ux, uy, uz])

def calcul_angle_beta(ccd_deg, tf_deg, delta_deg, gamma_deg, offset_mm):
    u = vecteur_col_abduction(ccd_deg, tf_deg, delta_deg, gamma_deg, offset_mm)
    ux, uz = u[0], u[2]
    norme_proj = np.sqrt(ux**2 + uz**2)
    cos_beta = ux / norme_proj
    beta_rad = np.arccos(cos_beta)
    return np.degrees(beta_rad)

def calcul_beta_corrige(beta_deg, av_deg):
    return beta_deg + av_deg

def calcul_delta_critique(ccd_deg, tf_deg, gamma_deg, offset_mm, av_deg, seuil_beta_corrige=10):
    for delta_deg in np.arange(0, 90, 0.1):
        beta = calcul_angle_beta(ccd_deg, tf_deg, delta_deg, gamma_deg, offset_mm)
        beta_corrige = calcul_beta_corrige(beta, av_deg)
        if beta_corrige <= seuil_beta_corrige:
            return round(delta_deg, 1)
    return 89.9

def calcul_reserve(delta_critique, delta_mesuree):
    return delta_critique - delta_mesuree

def interpretation_clinique(delta_critique, reserve, beta_corrige):
    if delta_critique == 89.9:
        return 'Pas de conflit — réserve infinie'
    elif reserve < 0:
        return 'Conflit — flexion critique dépassée'
    elif beta_corrige >= BETA_CONFLIT:
        return 'Conflit — flexion critique atteinte'
    elif reserve < 5:
        return 'Pas de conflit — réserve limitée'
    else:
        return 'Pas de conflit — réserve suffisante'

# --- Langues ---
langue = st.selectbox("🌐 Choisir la langue / Select language", ["Français", "English"])

labels = {
    "Français": {
        "title": "🦴 Analyse Clinique de la Réserve de Flexion",
        "patient_name": "Nom du patient",
        "tf": "Torsion fémorale (TF °)",
        "ccd": "Angle CCD (°)",
        "offset": "Offset fémoral (mm)",
        "abduction": "Abduction (γ + °)",
        "adduction": "Adduction (γ – °)",
        "version_stand": "Version debout (°)",
        "version_sit": "Version assis (°)",
        "anteversion": "Antéversion cotyle (AV °)",
        "mob": "Mobilité pelvienne (°)",
        "crit": "Flexion maximale tolérée (°)",
        "reserve": "Réserve de flexion (°)",
        "beta": "Angle β corrigé (°)",
        "export": "📥 Télécharger CSV",
        "export_pdf": "📄 Télécharger PDF",
        "attention": "⚠️ **Attention clinique** : Si la flexion pelvienne maximale tolérée (δ critique) est égale à 89.9°, cela signifie qu'aucun conflit n'est jamais détecté. Le calcul de la réserve n'est pas interprétable et ne doit pas être pris en compte dans l'analyse clinique.",
        "without_gamma": "Sans γ",
        "with_gamma": "Avec γ"
    },
    "English": {
        "title": "🦴 Clinical Analysis of Flexion Reserve",
        "patient_name": "Patient name",
        "tf": "Femoral torsion (TF °)",
        "ccd": "CCD angle (°)",
        "offset": "Femoral offset (mm)",
        "abduction": "Abduction (γ + °)",
        "adduction": "Adduction (γ – °)",
        "version_stand": "Standing version (°)",
        "version_sit": "Sitting version (°)",
        "anteversion": "Cup anteversion (AV °)",
        "mob": "Pelvic mobility (°)",
        "crit": "Max tolerated pelvic flexion (°)",
        "reserve": "Flexion reserve (°)",
        "beta": "Corrected β angle (°)",
        "export": "📥 Download CSV",
        "export_pdf": "📄 Download PDF",
        "attention": "⚠️ **Clinical warning**: If max tolerated pelvic flexion (δ critical) equals 89.9°, it means no conflict is ever detected. The reserve calculation is not interpretable and should not be used in clinical analysis.",
        "without_gamma": "Without γ",
        "with_gamma": "With γ"
    }
}[langue]

# Ici tu ajoutes les entrées Streamlit et calculs (inchangés)
# patient_name, delta_mesure, delta_critique_ref, reserve_ref, beta_corrige_ref, interpretation_ref, delta_critique_gamma, reserve_gamma, beta_corrige_gamma, interpretation_gamma, gamma_final

if st.button(labels["export_pdf"]):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, labels["title"].encode("latin-1", "replace").decode("latin-1"), ln=1)
    pdf.set_font("Arial", "", 12)

    text_content = f"""
{labels['patient_name']}: {{patient_name}}

{labels['without_gamma']} :
{labels['mob']}: {{delta_mesure:.1f}}°
{labels['crit']}: {{delta_critique_ref:.1f}}°
{labels['reserve']}: {{reserve_ref:.1f}}°
{labels['beta']}: {{beta_corrige_ref:.1f}}°
{{interpretation_ref}}

{labels['with_gamma']} = {{gamma_final:.1f}}° :
{labels['mob']}: {{delta_mesure:.1f}}°
{labels['crit']}: {{delta_critique_gamma:.1f}}°
{labels['reserve']}: {{reserve_gamma:.1f}}°
{labels['beta']}: {{beta_corrige_gamma:.1f}}°
{{interpretation_gamma}}
    """.format(
        patient_name=patient_name,
        delta_mesure=delta_mesure,
        delta_critique_ref=delta_critique_ref,
        reserve_ref=reserve_ref,
        beta_corrige_ref=beta_corrige_ref,
        interpretation_ref=interpretation_ref,
        gamma_final=gamma_final,
        delta_critique_gamma=delta_critique_gamma,
        reserve_gamma=reserve_gamma,
        beta_corrige_gamma=beta_corrige_gamma,
        interpretation_gamma=interpretation_gamma
    )

    for line in text_content.strip().splitlines():
        pdf.multi_cell(0, 10, line.encode("latin-1", "replace").decode("latin-1"))

    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    st.download_button(labels["export_pdf"], data=pdf_bytes, file_name="resultats_flexion.pdf", mime="application/pdf")

st.info(labels["attention"])
