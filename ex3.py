import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import re

# ====================
# Fonctions de Data Quality
# ====================

# Charger les données
def load_data(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        return pd.read_excel(uploaded_file)
    else:
        st.error("Format de fichier non pris en charge. Utilisez CSV ou Excel.")
        return None

# Analyse de la fraîcheur
def check_freshness(df, date_column, threshold_years=2):
    today = datetime.today()
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df['Obsolete'] = (today - df[date_column]).dt.days > (threshold_years * 365)
    obsolete_count = df['Obsolete'].sum()
    return df, obsolete_count

# Analyse des données manquantes
def check_missing_data(df, required_columns):
    missing_report = {}
    for col in required_columns:
        missing_count = df[col].isnull().sum()
        missing_percentage = (missing_count / len(df)) * 100
        missing_report[col] = {"missing_count": missing_count, "missing_percentage": missing_percentage}
    return pd.DataFrame(missing_report).T

# Validation des codes postaux
def validate_postal_code(df, postal_code_column, valid_length=5):
    df['Invalid_Code'] = df[postal_code_column].apply(
        lambda x: len(str(x)) != valid_length if pd.notnull(x) else True
    )
    invalid_count = df['Invalid_Code'].sum()
    return df[df['Invalid_Code']], invalid_count

# Validation des numéros de téléphone
def validate_phone_number(df, phone_column):
    phone_pattern = r'^\+?[1-9]\d{1,14}$'  # Format E.164
    df['Invalid_Phone'] = df[phone_column].apply(
        lambda x: not re.match(phone_pattern, str(x)) if pd.notnull(x) else True
    )
    invalid_count = df['Invalid_Phone'].sum()
    return df[df['Invalid_Phone']], invalid_count

# ====================
# Application Streamlit
# ====================

# Titre de l'application
st.title("Moteur de Qualité des Données avec Graphiques")

# Chargement du fichier
uploaded_file = st.file_uploader("Chargez un fichier CSV ou Excel", type=['csv', 'xls', 'xlsx'])

if uploaded_file:
    df = load_data(uploaded_file)
    if df is not None:
        st.write("### Aperçu des données", df.head())

        # Sélection des colonnes
        date_column = st.selectbox("Sélectionnez la colonne de date pour l'analyse de fraîcheur", df.columns)
        postal_code_column = st.selectbox("Sélectionnez la colonne des codes postaux", df.columns)
        phone_column = st.selectbox("Sélectionnez la colonne des numéros de téléphone", df.columns)
        required_columns = st.multiselect("Sélectionnez les colonnes obligatoires", df.columns)

        # Analyse de la fraîcheur
        st.subheader("Analyse de la Fraîcheur")
        df, obsolete_count = check_freshness(df, date_column)
        st.write(f"Enregistrements obsolètes : {obsolete_count}")
        freshness_chart = px.histogram(df, x='Obsolete', title="Répartition des Enregistrements Obsolètes")
        st.plotly_chart(freshness_chart)

        # Analyse des données manquantes
        st.subheader("Analyse des Données Manquantes")
        if required_columns:
            missing_report = check_missing_data(df, required_columns)
            st.write("Rapport des données manquantes :", missing_report)
            missing_chart = px.bar(
                missing_report.reset_index(),
                x="index",
                y="missing_percentage",
                title="Pourcentage des Données Manquantes par Colonne",
                labels={"index": "Colonnes", "missing_percentage": "Pourcentage Manquant"}
            )
            st.plotly_chart(missing_chart)
        else:
            st.warning("Veuillez sélectionner des colonnes obligatoires.")

        # Validation des codes postaux
        st.subheader("Validation des Codes Postaux")
        invalid_postal_codes, postal_issues = validate_postal_code(df, postal_code_column)
        st.write(f"Nombre de codes postaux invalides : {postal_issues}")
        postal_chart = px.bar(
            invalid_postal_codes[postal_code_column].value_counts().reset_index(),
            x="index",
            y=postal_code_column,
            title="Fréquence des Codes Postaux Invalides",
            labels={"index": "Code Postal", postal_code_column: "Fréquence"}
        )
        st.plotly_chart(postal_chart)

        # Validation des numéros de téléphone
        st.subheader("Validation des Numéros de Téléphone")
        invalid_phones, phone_issues = validate_phone_number(df, phone_column)
        st.write(f"Nombre de numéros de téléphone invalides : {phone_issues}")
        phone_chart = px.bar(
            invalid_phones[phone_column].value_counts().reset_index(),
            x="index",
            y=phone_column,
            title="Fréquence des Numéros de Téléphone Invalides",
            labels={"index": "Numéro de Téléphone", phone_column: "Fréquence"}
        )
        st.plotly_chart(phone_chart)
