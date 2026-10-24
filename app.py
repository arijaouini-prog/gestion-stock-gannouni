import streamlit as st
import pandas as pd
import os

# 1. Configuration de la page Streamlit
st.set_page_config(
    page_title="GestLab - Laboratoire Dr. Gannouni",
    page_icon="🧪",
    layout="wide"
)

EXCEL_FILE = "stock.xlsx"

# 2. Fonction pour charger les données Excel
@st.cache_data(ttl=1)
def charger_donnees():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE, sheet_name="Stock Automates")
    else:
        # Fallback si le fichier Excel n'est pas trouvé
        return pd.DataFrame([
            {"Code Réactif": "REA-BIO-001", "Automate": "Biochimie Auto-1", "Test / Paramètre": "Glycémie", "Stock Actuel (Flacons/Tests)": 500, "Consommation Test/Patient": 1, "Contrôles Std / Série": 1, "Seuil d'Alerte Stock": 100, "Emplacement / Statut": "En Stock", "Date Péremption": "2027-06-30"},
            {"Code Réactif": "REA-HEM-001", "Automate": "Hématologie Sysmex", "Test / Paramètre": "NFS (Formule Sanguine)", "Stock Actuel (Flacons/Tests)": 1200, "Consommation Test/Patient": 1, "Contrôles Std / Série": 2, "Seuil d'Alerte Stock": 200, "Emplacement / Statut": "En Stock", "Date Péremption": "2027-12-15"}
        ])

# 3. Fonction pour enregistrer dans le fichier Excel
def sauvegarder_donnees(df):
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Stock Automates", index=False)

# Chargement du stock
df_stock = charger_donnees()

# En-tête de l'application
st.title("🧪 GestLab - Laboratoire Dr. Gannouni")
st.caption("Système Intelligent de Gestion des Stocks & Détection du Gaspillage Réactifs")
st.markdown("---")

# 4. Barre latérale : Sélection de l'action
st.sidebar.header("⚙️ Opération à Effectuer")
action = st.sidebar.radio("Sélectionner l'action :", ["📥 Saisie d'Analyses (Déduire)", "➕ Réapprovisionnement (Ajouter)"])

automates_dispo = df_stock["Automate"].dropna().unique().tolist()
automate_choisi = st.sidebar.selectbox("1. Sélectionner l'Automate", automates_dispo)

tests_dispo = df_stock[df_stock["Automate"] == automate_choisi]["Test / Paramètre"].dropna().tolist()
test_choisi = st.sidebar.selectbox("2. Sélectionner le Test / Réactif", tests_dispo)

# Extraction des données du réactif sélectionné
index_reactif = df_stock[(df_stock["Automate"] == automate_choisi) & (df_stock["Test / Paramètre"] == test_choisi)].index[0]
stock_actuel = df_stock.loc[index_reactif, "Stock Actuel (Flacons/Tests)"]
controle_std = df_stock.loc[index_reactif, "Contrôles Std / Série"]
seuil_alerte = df_stock.loc[index_reactif, "Seuil d'Alerte Stock"]

# --- DÉROULEMENT SELON L'ACTION CHOISIE ---

if action == "📥 Saisie d'Analyses (Déduire)":
    nb_patients = st.sidebar.number_input("3. Nombre de Patients Réels", min_value=1, value=1, step=1)
    nb_calibrations = st.sidebar.number_input("4. Nombre de Calibrations/Contrôles Effectués", min_value=0, value=1, step=1)

    consommation_totale = (nb_patients * df_stock.loc[index_reactif, "Consommation Test/Patient"]) + nb_calibrations
    surconsommation = max(0, nb_calibrations - controle_std)

    # Bouton de validation pour déduction
    if st.sidebar.button("💾 Valider et Déduire du Stock"):
        nouveau_stock = stock_actuel - consommation_totale
        df_stock.loc[index_reactif, "Stock Actuel (Flacons/Tests)"] = nouveau_stock
        
        # Mise à jour automatique du statut
        if nouveau_stock <= seuil_alerte:
            df_stock.loc[index_reactif, "Emplacement / Statut"] = "Réapprovisionner"
        else:
            df_stock.loc[index_reactif, "Emplacement / Statut"] = "En Stock"
            
        sauvegarder_donnees(df_stock)
        st.sidebar.success(f"Stock mis à jour ! Nouveau stock : {nouveau_stock} tests.")
        st.cache_data.clear()

    # Affichage des 3 métriques principales
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Patients Traités", value=nb_patients)

    with col2:
        if nb_calibrations > controle_std:
            st.metric(
                label="Contrôles / Calibrations", 
                value=f"{nb_calibrations} effectués (Std: {controle_std})", 
                delta=f"+{surconsommation} en surconsommation", 
                delta_color="inverse"
            )
        else:
            st.metric(
                label="Contrôles / Calibrations", 
                value=f"{nb_calibrations} effectués (Std: {controle_std})", 
                delta="Consommation Conforme"
            )

    with col3:
        st.metric(label="Stock Restant pour ce Test", value=f"{stock_actuel} tests")

    # Alerte visuelle de gaspillage
    if nb_calibrations > controle_std:
        st.error(
            f"⚠️ **Alerte Gaspillage de Réactif !** Pour {nb_patients} patient(s), vous avez effectué **{nb_calibrations} calibrations/contrôles** alors que le standard de cet automate est de **{controle_std}**. "
            f"Cela génère une perte sèche de **{surconsommation} tests**."
        )
    else:
        st.success("✅ **Gestion Optimale :** Les ratios de calibration et de tests patients sont respectés.")

else:
    # Mode Réapprovisionnement (Ajout au stock)
    quantite_ajoutee = st.sidebar.number_input("3. Quantité de tests / flacons reçus", min_value=1, value=100, step=10)
    
    if st.sidebar.button("➕ Valider l'ajout au Stock"):
        nouveau_stock = stock_actuel + quantite_ajoutee
        df_stock.loc[index_reactif, "Stock Actuel (Flacons/Tests)"] = nouveau_stock
        
        # Mise à jour du statut
        if nouveau_stock > seuil_alerte:
            df_stock.loc[index_reactif, "Emplacement / Statut"] = "En Stock"
            
        sauvegarder_donnees(df_stock)
        st.sidebar.success(f"Stock réapprovisionné ! Nouveau stock : {nouveau_stock} tests.")
        st.cache_data.clear()

    # Métriques du réapprovisionnement
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Réactif Sélectionné", value=test_choisi)
    with col2:
        st.metric(label="Nouveau Stock Prévu", value=f"{stock_actuel + quantite_ajoutee} tests", delta=f"+{quantite_ajoutee} ajoutés")

st.markdown("---")

# 5. Tableau de bord interactif du stock
st.subheader("📦 État du Stock en Temps Réel (Synchronisé avec Excel)")

def highlight_status(val):
    if val == "Réapprovisionner":
        return 'background-color: #ffcccc; color: red; font-weight: bold;'
    elif val == "En Stock":
        return 'background-color: #e6ffe6; color: green;'
    return ''

st.dataframe(
    df_stock.style.map(highlight_status, subset=["Emplacement / Statut"]),
    use_container_width=True
)

# 6. Bouton de téléchargement du fichier Excel mis à jour
st.markdown("---")
if os.path.exists(EXCEL_FILE):
    with open(EXCEL_FILE, "rb") as file:
        st.download_button(
            label="📥 Télécharger le Fichier Excel du Stock à Jour (`stock_laboratoire_gannouni_exemple.xlsx`)",
            data=file,
            file_name="stock_laboratoire_gannouni_mis_a_jour.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.caption("💡 Application développée par **Arij Aouini** pour l'optimisation des flux de travail au Laboratoire Dr. Gannouni.")
