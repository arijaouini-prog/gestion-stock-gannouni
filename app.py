import streamlit as st
import pandas as pd
import os

# 1. Configuration de la page
st.set_page_config(
    page_title="GestLab - Laboratoire Dr. Gannouni",
    page_icon="🧪",
    layout="wide"
)

EXCEL_FILE = "stock_laboratoire_gannouni_exemple.xlsx"

# 2. Chargement optimisé du fichier Excel
@st.cache_data(ttl=1)
def charger_donnees():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE, sheet_name="Stock Automates")
    else:
        return pd.DataFrame([
            {"Code Réactif": "REA-BIO-001", "Automate": "Biochimie Auto-1", "Test / Paramètre": "Glycémie", "Stock Actuel (Flacons/Tests)": 500, "Consommation Test/Patient": 1, "Contrôles Std / Série": 1, "Seuil d'Alerte Stock": 100, "Emplacement / Statut": "En Stock", "Date Péremption": "2027-06-30"},
            {"Code Réactif": "REA-HEM-001", "Automate": "Hématologie Sysmex", "Test / Paramètre": "NFS (Formule Sanguine)", "Stock Actuel (Flacons/Tests)": 1200, "Consommation Test/Patient": 1, "Contrôles Std / Série": 2, "Seuil d'Alerte Stock": 200, "Emplacement / Statut": "En Stock", "Date Péremption": "2027-12-15"}
        ])

def sauvegarder_donnees(df):
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Stock Automates", index=False)

df_stock = charger_donnees()

# En-tête de l'application
st.title("🧪 GestLab - Suivi Ciblé du Stock & Automates")
st.caption("Laboratoire Dr. Gannouni — Système d'optimisation des réactifs")
st.markdown("---")

# 3. Barre latérale : Sélection de l'opération
st.sidebar.header("⚙️ Saisie Rapide")
action = st.sidebar.radio("Opération :", ["📥 Saisie d'Analyses (Déduire)", "➕ Réapprovisionnement (Ajouter)"])

automates_dispo = df_stock["Automate"].dropna().unique().tolist()
automate_choisi = st.sidebar.selectbox("1. Choisir l'Automate", automates_dispo)

tests_dispo = df_stock[df_stock["Automate"] == automate_choisi]["Test / Paramètre"].dropna().tolist()
test_choisi = st.sidebar.selectbox("2. Choisir le Test / Réactif", tests_dispo)

# Extraction ciblée de la ligne sélectionnée (sans afficher tout le tableau)
index_reactif = df_stock[(df_stock["Automate"] == automate_choisi) & (df_stock["Test / Paramètre"] == test_choisi)].index[0]
ligne_selectionnee = df_stock.loc[index_reactif]

stock_actuel = ligne_selectionnee["Stock Actuel (Flacons/Tests)"]
seuil_alerte = ligne_selectionnee["Seuil d'Alerte Stock"]
controle_std = ligne_selectionnee["Contrôles Std / Série"]

# --- SECTION PRINCIPALE : Fiche du Réactif Sélectionné Uniquement ---
st.subheader(f"📌 Fiche du Réactif : {test_choisi} ({automate_choisi})")

col_a, col_b, col_c = st.columns(3)
col_a.metric("Stock Actuel", f"{stock_actuel} tests")
col_b.metric("Seuil Critique d'Alerte", f"{seuil_alerte} tests")
col_c.metric("Statut Actuel", ligne_selectionnee["Emplacement / Statut"])

st.markdown("---")

# --- TRAITEMENT DES OPÉRATIONS ---
if action == "📥 Saisie d'Analyses (Déduire)":
    st.subheader("📝 Traitement de la série d'analyses")
    col1, col2 = st.columns(2)
    
    with col1:
        nb_patients = st.number_input("Nombre de Patients Réels", min_value=1, value=1, step=1)
    with col2:
        nb_calibrations = st.number_input("Nombre de Calibrations/Contrôles Effectués", min_value=0, value=1, step=1)
        
    consommation_totale = (nb_patients * ligne_selectionnee["Consommation Test/Patient"]) + nb_calibrations
    surconsommation = max(0, nb_calibrations - controle_std)

    # Détection immédiate du gaspillage
    if nb_calibrations > controle_std:
        st.error(f"⚠️ **Alerte Surconsommation !** Vous effectuez {nb_calibrations} contrôles pour {nb_patients} patient(s). Le standard pour cet automate est de {controle_std} contrôle(s). Perte : **+{surconsommation} tests**.")
    else:
        st.success("✅ Ratio de calibration conforme aux exigences techniques.")

    if st.button("💾 Valider la Déduction du Stock"):
        nouveau_stock = stock_actuel - consommation_totale
        df_stock.loc[index_reactif, "Stock Actuel (Flacons/Tests)"] = nouveau_stock
        df_stock.loc[index_reactif, "Emplacement / Statut"] = "Réapprovisionner" if nouveau_stock <= seuil_alerte else "En Stock"
        
        sauvegarder_donnees(df_stock)
        st.success(f"Opération enregistrée ! Nouveau stock pour {test_choisi} : **{nouveau_stock} tests**.")
        st.cache_data.clear()

else:
    st.subheader("📦 Entrée en Stock (Réapprovisionnement)")
    quantite_ajoutee = st.number_input("Quantité de tests / flacons reçus", min_value=1, value=100, step=10)
    
    if st.button("➕ Valider l'ajout au Stock"):
        nouveau_stock = stock_actuel + quantite_ajoutee
        df_stock.loc[index_reactif, "Stock Actuel (Flacons/Tests)"] = nouveau_stock
        df_stock.loc[index_reactif, "Emplacement / Statut"] = "En Stock"
        
        sauvegarder_donnees(df_stock)
        st.success(f"Stock mis à jour ! Nouveau stock pour {test_choisi} : **{nouveau_stock} tests**.")
        st.cache_data.clear()

st.markdown("---")

# --- SECTION D'ALERTE : Afficher SEULEMENT les réactifs en manque ---
st.subheader("🚨 Alertes Réapprovisionnement Uniquement")

df_alertes = df_stock[df_stock["Emplacement / Statut"] == "Réapprovisionner"]

if not df_alertes.empty:
    st.warning("Certains réactifs ont atteint leur seuil d'alerte critique :")
    # On n'affiche que les colonnes indispensables pour les alertes
    st.dataframe(
        df_alertes[["Automate", "Test / Paramètre", "Stock Actuel (Flacons/Tests)", "Seuil d'Alerte Stock", "Emplacement / Statut"]],
        use_container_width=True
    )
else:
    st.success("🎉 Tous les réactifs sont au-dessus de leur seuil d'alerte.")

st.markdown("---")

# Téléchargement optionnel du fichier Excel complet en arrière-plan
if os.path.exists(EXCEL_FILE):
    with open(EXCEL_FILE, "rb") as file:
        st.download_button(
            label="📥 Exporter le fichier Excel complet du Stock (`stock.xlsx`)",
            data=file,
            file_name="stock_laboratoire_gannouni_mis_a_jour.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
