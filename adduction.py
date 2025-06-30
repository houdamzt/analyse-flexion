import streamlit as st
import numpy as np
import math
import pandas as pd

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

# --- Interface ---
st.title("🦴 Analyse Clinique de la Réserve de Flexion")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📐 Paramètres pelviens")
    version_debout = st.number_input("Version debout (°)", value=15.0)
    version_assis = st.number_input("Version assis (°)", value=35.0)
    anteversion = st.number_input("Antéversion cotyle (AV °)", value=25.0)

with col2:
    st.subheader("🦵 Paramètres fémoraux")
    tf = st.number_input("Torsion fémorale (TF °)", value=20.0)
    ccd = st.number_input("Angle CCD (°)", value=130.0)
    offset = st.number_input("Offset fémoral (mm)", value=40.0)
    abduction = st.slider("Abduction (γ + °)", min_value=0.0, max_value=30.0, step=1.0, value=0.0)
    adduction = st.slider("Adduction (γ – °)", min_value=0.0, max_value=30.0, step=1.0, value=0.0)

# --- Calcul principal ---
delta_mesure = version_assis - version_debout

# Référence γ = 0
delta_critique_ref = calcul_delta_critique(ccd, tf, 0.0, offset, anteversion)
reserve_ref = calcul_reserve(delta_critique_ref, delta_mesure)
beta_ref = calcul_angle_beta(ccd, tf, delta_mesure, 0.0, offset)
beta_corrige_ref = calcul_beta_corrige(beta_ref, anteversion)
interpretation_ref = interpretation_clinique(delta_critique_ref, reserve_ref, beta_corrige_ref)

# γ final choisi (positif abduction, négatif adduction)
gamma_final = abduction - adduction

delta_critique_gamma = calcul_delta_critique(ccd, tf, gamma_final, offset, anteversion)
reserve_gamma = calcul_reserve(delta_critique_gamma, delta_mesure)
beta_gamma = calcul_angle_beta(ccd, tf, delta_mesure, gamma_final, offset)
beta_corrige_gamma = calcul_beta_corrige(beta_gamma, anteversion)
interpretation_gamma = interpretation_clinique(delta_critique_gamma, reserve_gamma, beta_corrige_gamma)

# --- Résultats comparés ---
st.subheader("📊 Résultats comparés")

col_ref, col_gamma = st.columns(2)

with col_ref:
    st.markdown("### ✅ Sans abduction/adduction (γ = 0°)")
    st.markdown(f"- **Mobilité pelvienne (°)** : `{delta_mesure:.1f}°`")
    st.markdown(f"- **Flexion pelvienne maximale tolérée (°)** : `{delta_critique_ref:.1f}°`")
    st.markdown(f"- **Réserve de flexion** : `{reserve_ref:.1f}°`")
    st.markdown(f"- **Angle β corrigé** : `{beta_corrige_ref:.1f}°`")
    st.markdown(f"#### 🩺 _{interpretation_ref}_")

with col_gamma:
    st.markdown(f"### 🔄 Avec γ = {gamma_final:.1f}°")
    st.markdown(f"- **Mobilité pelvienne (°)** : `{delta_mesure:.1f}°`")
    st.markdown(f"- **Flexion pelvienne maximale tolérée (°)** : `{delta_critique_gamma:.1f}°`")
    st.markdown(f"- **Réserve de flexion** : `{reserve_gamma:.1f}°`")
    st.markdown(f"- **Angle β corrigé** : `{beta_corrige_gamma:.1f}°`")
    st.markdown(f"#### 🩺 _{interpretation_gamma}_")

# --- Avertissement ---
st.info(
    "⚠️ **Attention clinique** : "
    "Si la flexion pelvienne maximale tolérée (δ critique) est égale à 89.9°, "
    "cela signifie qu'aucun conflit n'est jamais détecté. Le calcul de la réserve "
    "n'est donc pas interprétable et ne doit pas être pris en compte dans l'analyse clinique."
)

# --- Export CSV ---
if st.button("💾 Exporter les résultats en CSV"):
    df = pd.DataFrame({
        "Condition": ["Sans γ", f"Avec γ = {gamma_final:.1f}°"],
        "Mobilité pelvienne (°)": [delta_mesure, delta_mesure],
        "Flexion maximale tolérée (°)": [delta_critique_ref, delta_critique_gamma],
        "Réserve de flexion (°)": [reserve_ref, reserve_gamma],
        "Angle β corrigé (°)": [beta_corrige_ref, beta_corrige_gamma],
        "Interprétation clinique": [interpretation_ref, interpretation_gamma],
    })
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Télécharger CSV", data=csv, file_name="resultats_flexion.csv", mime="text/csv")
