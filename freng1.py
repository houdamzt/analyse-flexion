import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import math

# --- Constantes ---
BETA_CONFLIT = 10

# --- Fonctions ---
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

# --- Langue ---
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
        "attention": "⚠️ **Attention clinique** : Si la flexion pelvienne maximale tolérée (δ critique) est égale à 89.9°, cela signifie qu'aucun conflit n'est jamais détecté. Le calcul de la réserve n'est pas interprétable et ne doit pas être pris en compte dans l'analyse clinique."
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
        "attention": "⚠️ **Clinical warning**: If max tolerated pelvic flexion (δ critical) equals 89.9°, it means no conflict is ever detected. The reserve calculation is not interpretable and should not be used in clinical analysis."
    }
}[langue]

st.title(labels["title"])
patient_name = st.text_input(labels["patient_name"], value="Patient X")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Pelvien / Pelvic")
    version_debout = st.number_input(labels["version_stand"], value=15.0, step=1.0)
    version_assis = st.number_input(labels["version_sit"], value=35.0, step=1.0)
    anteversion = st.number_input(labels["anteversion"], value=25.0, step=1.0)

with col2:
    st.subheader("Fémoral / Femoral")
    tf = st.number_input(labels["tf"], value=20.0, step=1.0)
    ccd = st.number_input(labels["ccd"], value=130.0, step=1.0)
    offset = st.number_input(labels["offset"], value=40.0, step=1.0)
    abduction = st.number_input(labels["abduction"], min_value=0.0, max_value=30.0, value=0.0, step=1.0)
    adduction = st.number_input(labels["adduction"], min_value=0.0, max_value=30.0, value=0.0, step=1.0)

gamma_final = abduction - adduction
delta_mesure = version_assis - version_debout

delta_critique_ref = calcul_delta_critique(ccd, tf, 0.0, offset, anteversion)
reserve_ref = calcul_reserve(delta_critique_ref, delta_mesure)
beta_ref = calcul_angle_beta(ccd, tf, delta_mesure, 0.0, offset)
beta_corrige_ref = calcul_beta_corrige(beta_ref, anteversion)
interpretation_ref = interpretation_clinique(delta_critique_ref, reserve_ref, beta_corrige_ref)

delta_critique_gamma = calcul_delta_critique(ccd, tf, gamma_final, offset, anteversion)
reserve_gamma = calcul_reserve(delta_critique_gamma, delta_mesure)
beta_gamma = calcul_angle_beta(ccd, tf, delta_mesure, gamma_final, offset)
beta_corrige_gamma = calcul_beta_corrige(beta_gamma, anteversion)
interpretation_gamma = interpretation_clinique(delta_critique_gamma, reserve_gamma, beta_corrige_gamma)

df = pd.DataFrame({
    "Condition": ["Sans γ", f"Avec γ = {gamma_final:.1f}°"],
    labels["mob"]: [delta_mesure, delta_mesure],
    labels["crit"]: [delta_critique_ref, delta_critique_gamma],
    labels["reserve"]: [reserve_ref, reserve_gamma],
    labels["beta"]: [beta_corrige_ref, beta_corrige_gamma],
    "Interprétation": [interpretation_ref, interpretation_gamma],
    labels["patient_name"]: [patient_name, patient_name]
})

# --- Export CSV ---
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(labels["export"], data=csv, file_name="resultats_flexion.csv", mime="text/csv")

# --- Export PDF ---
if st.button(labels["export_pdf"]):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, labels["title"], ln=1)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, f"Nom du patient / Patient name: {patient_name}\n\n{df.to_string(index=False)}")
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    st.download_button("📄 Télécharger PDF", data=pdf_output.getvalue(), file_name="resultats_flexion.pdf", mime="application/pdf")

st.info(labels["attention"])
