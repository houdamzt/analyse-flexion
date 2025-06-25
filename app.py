import streamlit as st
import numpy as np
import pandas as pd
import math

# --- Constantes ---
BETA_CONFLIT = 10  # seuil critique pour conflit, en degrés

# --- Fonctions de calculs ---
def calcul_delta_critique_beta10(tf_deg, ccd_deg, offset_mm, av_cotyle_deg, seuil_beta_corrige=10):
    for delta_deg in np.arange(0, 90, 0.1):
        beta = calcul_angle_beta(ccd_deg, tf_deg, delta_deg, offset_mm)
        beta_corrige = calcul_beta_corrige(beta, av_cotyle_deg)
        if beta_corrige <= seuil_beta_corrige:
            return round(delta_deg, 1)
    return 89.9  # Non trouvé

def estimer_longueur_col_femoral(offset_mm, ccd_deg):
    ccd_rad = np.radians(ccd_deg)
    return offset_mm / np.sin(ccd_rad)

def vecteur_col_bascule(ccd_deg, tf_deg, delta_deg, long_col):
    CCD = np.radians(ccd_deg)
    tf = np.radians(tf_deg)
    delta = np.radians(delta_deg)
    ux = np.sin(math.pi - CCD) * long_col
    uy = (np.cos(delta) * np.cos(math.pi - CCD) * long_col) - (np.sin(delta) * np.sin(tf) * long_col)
    uz = (-np.sin(delta) * np.cos(math.pi - CCD) * long_col) + (np.cos(delta) * np.sin(tf) * long_col)
    return np.array([ux, uy, uz])

def calcul_angle_beta(ccd_deg, tf_deg, delta_deg, offset_mm):
    long_col = estimer_longueur_col_femoral(offset_mm, ccd_deg)
    u = vecteur_col_bascule(ccd_deg, tf_deg, delta_deg, long_col)
    ux, uz = u[0], u[2]
    norme_proj = np.sqrt(ux**2 + uz**2)
    cos_beta = ux / norme_proj
    beta_rad = np.arccos(cos_beta)
    return np.degrees(beta_rad)

def calcul_beta_corrige(beta_deg, av_cotyle_deg):
    return beta_deg + av_cotyle_deg

def calcul_reserve_flexion(delta_critique, delta_mesure):
    return delta_critique - delta_mesure

def interpretation_clinique(delta_critique, reserve_flexion, beta_corrige):
    if delta_critique == 89.9:
        return 'Pas de conflit — réserve infinie'
    elif reserve_flexion < 0:
        return 'Conflit — flexion critique dépassée'
    elif beta_corrige >= BETA_CONFLIT:
        return 'Conflit — flexion critique atteinte'
    elif reserve_flexion < 5:
        return 'Pas de conflit — réserve limitée'
    else:
        return 'Pas de conflit — réserve suffisante'

# --- Interface utilisateur ---
st.title("🦴 Analyse Clinique de la Réserve de Flexion")

st.header("📋 Paramètres du patient")
tf_deg = st.number_input("TF (°)", value=20.0)
ccd_deg = st.number_input("CCD (°)", value=130.0)
version_debout = st.number_input("Version debout (°)", value=15.0)
version_assis = st.number_input("Version assis (°)", value=35.0)
anteversion_assis = st.number_input("Antéversion assis (°)", value=30.0)
offset_mm = st.number_input("Femoral Offset (mm)", value=40.0)

# --- Calculs ---
if st.button("Analyser"):
    delta_mesure = version_assis - version_debout
    delta_critique = calcul_delta_critique_beta10(tf_deg, ccd_deg, offset_mm, anteversion_assis)
    reserve = calcul_reserve_flexion(delta_critique, delta_mesure)
    beta = calcul_angle_beta(ccd_deg, tf_deg, delta_mesure, offset_mm)
    beta_corrige = calcul_beta_corrige(beta, anteversion_assis)
    interpretation = interpretation_clinique(delta_critique, reserve, beta_corrige)

    # --- Affichage des résultats ---
    st.subheader("🧾 Résultats de l'analyse")
    st.markdown(f"**Delta mesuré :** {delta_mesure:.1f}°")
    st.markdown(f"**Delta critique :** {delta_critique:.1f}°")
    st.markdown(f"**Réserve de flexion :** {reserve:.1f}°")
    st.markdown(f"**Angle beta corrigé :** {beta_corrige:.1f}°")
    st.markdown(f"**🩺 Interprétation clinique :** _{interpretation}_")
