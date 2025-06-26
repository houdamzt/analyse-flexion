import streamlit as st
import numpy as np
import math

# --- Constantes ---
BETA_CONFLIT = 10  # Seuil critique en degrés

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

# --- Interface utilisateur ---
st.title("🦴 Simulation de la Réserve de Flexion avec Abduction (γ)")

st.sidebar.header("🔧 Paramètres patient")
tf = st.sidebar.number_input("Torsion fémorale (TF °)", value=20.0)
ccd = st.sidebar.number_input("Angle CCD (°)", value=130.0)
offset = st.sidebar.number_input("Offset fémoral (mm)", value=40.0)
version_debout = st.sidebar.number_input("Version debout (°)", value=15.0)
version_assis = st.sidebar.number_input("Version assis (°)", value=35.0)
anteversion = st.sidebar.number_input("Antéversion cotyle (AV °)", value=25.0)
gamma = st.sidebar.slider("Abduction (γ °)", min_value=0.0, max_value=30.0, step=1.0, value=0.0)

# --- Calculs ---
delta_mesure = version_assis - version_debout
delta_critique = calcul_delta_critique(ccd, tf, gamma, offset, anteversion)
reserve = calcul_reserve(delta_critique, delta_mesure)
beta = calcul_angle_beta(ccd, tf, delta_mesure, gamma, offset)
beta_corrige = calcul_beta_corrige(beta, anteversion)
interpretation = interpretation_clinique(delta_critique, reserve, beta_corrige)

# --- Résultats ---
st.header("📊 Résultats")
st.markdown(f"**Delta mesuré :** {delta_mesure:.1f}°")
st.markdown(f"**Delta critique :** {delta_critique:.1f}°")
st.markdown(f"**Réserve de flexion :** {reserve:.1f}°")
st.markdown(f"**Angle β corrigé :** {beta_corrige:.1f}°")
st.markdown(f"**🩺 Interprétation clinique :** _{interpretation}_")
