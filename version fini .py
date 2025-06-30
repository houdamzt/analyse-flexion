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
        return labels["no_conflict"]
    elif reserve < 0:
        return labels["conflict_critical_exceeded"]
    elif beta_corrige >= BETA_CONFLIT:
        return labels["conflict_critical_reached"]
    elif reserve < 5:
        return labels["no_conflict_limited"]
    else:
        return labels["no_conflict_sufficient"]

# --- Nouvelles fonctions pour flexion jambe ---
def calcul_angle_beta_alpha(ccd_deg, tf_deg, alpha_deg, offset_mm, gamma_deg=0):
    ccd_rad = np.radians(ccd_deg)
    tf_rad = np.radians(tf_deg)
    alpha_rad = np.radians(alpha_deg)
    gamma_rad = np.radians(gamma_deg)
    long_col = offset_mm / np.sin(ccd_rad)

    ux = np.sin(math.pi - ccd_rad + gamma_rad) * long_col
    uy = -np.cos(alpha_rad) * np.cos(math.pi - ccd_rad + gamma_rad) * long_col - np.sin(alpha_rad) * np.sin(tf_rad) * long_col
    uz = -np.sin(alpha_rad) * np.cos(math.pi - ccd_rad + gamma_rad) * long_col + np.cos(alpha_rad) * np.sin(tf_rad) * long_col
    norme_proj = np.sqrt(ux**2 + uz**2)
    cos_beta = ux / norme_proj
    beta_rad = np.arccos(cos_beta)
    return np.degrees(beta_rad)

def calcul_alpha_critique(tf_deg, ccd_deg, offset_mm, av_cotyle_deg, gamma_deg=0, seuil_beta_corrige=10):
    for alpha_deg in np.arange(0, 130, 0.1):
        beta = calcul_angle_beta_alpha(ccd_deg, tf_deg, alpha_deg, offset_mm, gamma_deg)
        beta_corrige = calcul_beta_corrige(beta, av_cotyle_deg)
        if beta_corrige <= seuil_beta_corrige:
            return round(alpha_deg, 1)
    return 129.9


def calcul_alpha_critique_sans_gamma(tf_deg, ccd_deg, offset_mm, av_cotyle_deg, seuil_beta_corrige=10):
    for alpha_deg in np.arange(0, 130, 0.1):
        beta = calcul_angle_beta_alpha(ccd_deg, tf_deg, alpha_deg, offset_mm, gamma_deg=0)
        beta_corrige = calcul_beta_corrige(beta, av_cotyle_deg)
        if beta_corrige <= seuil_beta_corrige:
            return round(alpha_deg, 1)
    return 129.9

# --- Langues ---
langue = st.selectbox("🌐 Choisir la langue / Select language", ["Français", "English"])

labels = {
    "Français": {
        "title": " Analyse Clinique de la Réserve de Flexion",
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
        "beta": "Inclinaison col fémoral (°)",
        "export": "📥 Télécharger CSV",
        "export_pdf": "📄 Télécharger PDF",
        "attention": "⚠️ **Attention clinique** : Si la flexion pelvienne maximale tolérée (δ critique) est égale à 89.9°, cela signifie qu'aucun conflit n'est jamais détecté. Dans ce cas, la réserve est considérée comme infinie, car la flexion pelvienne est totalement libre et il n’existe aucune limite fonctionnelle.",
        "results_analysis": "Résultats d’analyse",
        "results_flexion_leg": "Résultats flexion jambe",
        "without_gamma": "Sans adduction/abduction (γ = 0°)",
        "with_gamma": "Avec adduction/abduction (γ = {gamma:.1f}°)",
        "alpha_measured": "Flexion de hanche mesurée",
        "alpha_crit": "Flexion maximal théorique avant comflit",
        "risk_none": "Pas de risque de luxation : Réserve infinie",
        "risk_limited": "Risque de luxation : Réserve limitée",
        "no_conflict": "Pas de conflit : réserve infinie",
        "conflict_critical_exceeded": "Conflit : flexion critique dépassée",
        "conflict_critical_reached": "Conflit : flexion critique atteinte",
        "no_conflict_limited": "Pas de conflit : réserve limitée",
        "no_conflict_sufficient": "Pas de conflit : réserve suffisante"
    },
    "English": {
        "title": " Clinical Analysis of Flexion Reserve",
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
        "beta": "Femoral neck inclination (°)",
        "export": "📥 Download CSV",
        "export_pdf": "📄 Download PDF",
        "attention": "⚠️ **Clinical warning**: If the maximum tolerated pelvic flexion (δ critical) is equal to 89.9°, this means that no conflict is ever detected. In this case, the flexion reserve is considered infinite, as pelvic flexion is completely free and there is no functional limitation.",
        "results_analysis": "Analysis results",
        "results_flexion_leg": "Leg flexion results",
        "without_gamma": "Without adduction/abduction (γ = 0°)",
        "with_gamma": "With adduction/abduction (γ = {gamma:.1f}°)",
        "alpha_measured": "Measured hip flexion",
        "alpha_crit": "Maximum theoretical flexion before impingement",
        "risk_none": "No dislocation risk: Infinite reserve",
        "risk_limited": "Dislocation risk: Limited reserve",
        "no_conflict": "No conflict: Infinite reserve",
        "conflict_critical_exceeded": "Conflict: Critical flexion exceeded",
        "conflict_critical_reached": "Conflict: Critical flexion reached",
        "no_conflict_limited": "No conflict: Limited reserve",
        "no_conflict_sufficient": "No conflict: Sufficient reserve"
    }
}[langue]


st.title(labels["title"])
patient_name = st.text_input(labels["patient_name"], value="Patient X")


col1, col2 = st.columns(2)

with col1:
    
    st.subheader("Paramètres pelviens / Pelvic parameters")
    version_debout = st.number_input(labels["version_stand"], value=15.0, step=1.0)
    version_assis = st.number_input(labels["version_sit"], value=35.0, step=1.0)
    anteversion = st.number_input(labels["anteversion"], value=25.0, step=1.0)
    alpha_mesure = st.number_input("Alpha mesuré (°)", value=90.0, step=1.0)

with col2:
    st.subheader("Paramètres fémoraux / Femoral parameters")
    tf = st.number_input(labels["tf"], value=20.0, step=1.0)
    ccd = st.number_input(labels["ccd"], value=130.0, step=1.0)
    offset = st.number_input(labels["offset"], value=40.0, step=1.0)
    gamma_final = st.slider(
    "Abduction (+) / Adduction (–) (γ °)", 
    min_value=-45.0, 
    max_value=45.0, 
    value=0.0, 
    step=1.0,
    help="Valeurs négatives : adduction, valeurs positives : abduction"
)

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

# --- 💥 Nouveau calcul pour flexion jambe ---

alpha_critique_avec_gamma = calcul_alpha_critique(tf, ccd, offset, anteversion, gamma_final)
reserve_alpha_avec_gamma = alpha_critique_avec_gamma - alpha_mesure

if alpha_critique_avec_gamma == 129.9:
    interpretation_alpha_avec = labels["risk_none"]
else:
    interpretation_alpha_avec = labels["risk_limited"]


alpha_critique_sans_gamma = calcul_alpha_critique_sans_gamma(tf, ccd, offset, anteversion)
reserve_alpha_sans_gamma = alpha_critique_sans_gamma - alpha_mesure

if alpha_critique_sans_gamma == 129.9:
    interpretation_alpha_sans = labels["risk_none"]
else:
    interpretation_alpha_sans = labels["risk_limited"]



# --- Affichage joli en colonnes (corrigé) ---
with st.container():
    st.subheader("Résultats d’analyse" if langue == "Français" else "Analysis results")
    st.subheader("Flexion du tronc" if langue == "Français" else "Trunk flexion")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**" + (f"Sans abduction/adduction (γ = {0.0:.1f}°)" if langue == "Français" else f"Without abduction/adduction (γ = {0.0:.1f}°)") + "**")
    st.write(f"• {labels['mob']}: :green[{delta_mesure:.1f}°]")
    st.write(f"• {labels['crit']}: :green[{delta_critique_ref:.1f}°]")
    st.write(f"• {labels['reserve']}: :green[{reserve_ref:.1f}°]")
    st.write(f"• {labels['beta']}: :green[{beta_corrige_ref:.1f}°]")
    st.markdown(f"*{interpretation_ref}*")

with col2:
    st.markdown("**" + (f"Avec abduction/adduction (γ = {gamma_final:.1f}°)" if langue == "Français" else f"With abduction/adduction (γ = {gamma_final:.1f}°)") + "**")
    st.write(f"• {labels['mob']}: :green[{delta_mesure:.1f}°]")
    st.write(f"• {labels['crit']}: :green[{delta_critique_gamma:.1f}°]")
    st.write(f"• {labels['reserve']}: :green[{reserve_gamma:.1f}°]")
    st.write(f"• {labels['beta']}: :green[{beta_corrige_gamma:.1f}°]")
    st.markdown(f"*{interpretation_gamma}*")

# --- Résultats flexion jambe ---
st.subheader("Résultats flexion jambe" if langue == "Français" else "Leg flexion results")

col3, col4 = st.columns(2)

# Labels
alpha_mesure_label = 'Alpha mesuré' if langue == 'Français' else 'Measured alpha'
alpha_critique_label = 'Alpha critique' if langue == 'Français' else 'Critical alpha'
reserve_flexion_label = 'Réserve de flexion' if langue == 'Français' else 'Flexion reserve'

with col3:
    st.markdown("**" + ("Sans abduction/adduction (γ = 0°)" if langue == "Français" else "Without gamma (γ = 0°)") + "**")
    st.write(f"• {alpha_mesure_label} : :green[{alpha_mesure:.1f}°]")
    st.write(f"• {alpha_critique_label} : :green[{alpha_critique_sans_gamma:.1f}°]")
    st.write(f"• {reserve_flexion_label} : :green[{reserve_alpha_sans_gamma:.1f}°]")
    st.markdown(f"*{interpretation_alpha_sans}*")

with col4:
    st.markdown("**" + (f"Avec abduction/adduction (γ = {gamma_final:.1f}°)" if langue == "Français" else f"With gamma (γ = {gamma_final:.1f}°)") + "**")
    st.write(f"• {alpha_mesure_label} : :green[{alpha_mesure:.1f}°]")
    st.write(f"• {alpha_critique_label} : :green[{alpha_critique_avec_gamma:.1f}°]")
    st.write(f"• {reserve_flexion_label} : :green[{reserve_alpha_avec_gamma:.1f}°]")
    st.markdown(f"*{interpretation_alpha_avec}*")

# --- Export CSV ---

df = pd.DataFrame({
    "Condition": ["Sans abduction/adduction", f"Avec abduction/adduction = {gamma_final:.1f}°"],
    labels["mob"]: [delta_mesure, delta_mesure],
    labels["crit"]: [delta_critique_ref, delta_critique_gamma],
    labels["reserve"]: [reserve_ref, reserve_gamma],
    labels["beta"]: [beta_corrige_ref, beta_corrige_gamma],
    "Interprétation": [interpretation_ref, interpretation_gamma],
    labels["patient_name"]: [patient_name, patient_name]
})

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(labels["export"], data=csv, file_name="resultats_flexion.csv", mime="text/csv")

if st.button(labels["export_pdf"]):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, labels["title"].encode("latin-1", "replace").decode("latin-1"), ln=1)
    pdf.set_font("Arial", "", 12)

    # --- Résultats tronc ---
    text_content = f"""
    {labels['patient_name']}: {patient_name}

    Sans abduction/adduction :
    {labels['mob']}: {delta_mesure:.1f}°
    {labels['crit']}: {delta_critique_ref:.1f}°
    {labels['reserve']}: {reserve_ref:.1f}°
    {labels['beta']}: {beta_corrige_ref:.1f}°
    {interpretation_ref}

    Avec abduction/adduction = {gamma_final:.1f}° :
    {labels['mob']}: {delta_mesure:.1f}°
    {labels['crit']}: {delta_critique_gamma:.1f}°
    {labels['reserve']}: {reserve_gamma:.1f}°
    {labels['beta']}: {beta_corrige_gamma:.1f}°
    {interpretation_gamma}
    """

    # Ajout ligne par ligne en filtrant
    for line in text_content.strip().splitlines():
        safe_line = line.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 10, safe_line)

    # --- Résultats flexion jambe ---
    pdf.multi_cell(0, 10, (labels["results_flexion_leg"]).encode("latin-1", "replace").decode("latin-1"))
    pdf.multi_cell(0, 10, (labels["without_gamma"]).encode("latin-1", "replace").decode("latin-1"))
    pdf.multi_cell(0, 10, f"{labels['alpha_measured']} : {alpha_mesure:.1f}°".encode("latin-1", "replace").decode("latin-1"))
    pdf.multi_cell(0, 10, f"{labels['alpha_crit']} : {alpha_critique_sans_gamma:.1f}°".encode("latin-1", "replace").decode("latin-1"))
    pdf.multi_cell(0, 10, f"{labels['reserve']} : {reserve_alpha_sans_gamma:.1f}°".encode("latin-1", "replace").decode("latin-1"))
    pdf.multi_cell(0, 10, interpretation_alpha_sans.encode("latin-1", "replace").decode("latin-1"))

    pdf.multi_cell(0, 10, (labels["with_gamma"].format(gamma=gamma_final)).encode("latin-1", "replace").decode("latin-1"))
    pdf.multi_cell(0, 10, f"{labels['alpha_measured']} : {alpha_mesure:.1f}°".encode("latin-1", "replace").decode("latin-1"))
    pdf.multi_cell(0, 10, f"{labels['alpha_crit']} : {alpha_critique_avec_gamma:.1f}°".encode("latin-1", "replace").decode("latin-1"))
    pdf.multi_cell(0, 10, f"{labels['reserve']} : {reserve_alpha_avec_gamma:.1f}°".encode("latin-1", "replace").decode("latin-1"))
    pdf.multi_cell(0, 10, interpretation_alpha_avec.encode("latin-1", "replace").decode("latin-1"))

    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
    st.download_button(labels["export_pdf"], data=pdf_bytes, file_name="resultats_flexion.pdf", mime="application/pdf")

st.info(labels["attention"])

