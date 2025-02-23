import streamlit as st
import pandas as pd
from datetime import datetime
import re
import pycountry
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from functions import *

# Fonctions pour charger les données
def load_data(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        return pd.read_excel(uploaded_file)
    else:
        st.error("Format de fichier non pris en charge. Utilisez CSV ou Excel.")
        return None

# Fonctions de validation (déjà fournies dans le code)

# Fonction principale Streamlit
def main():
    st.title("Application de Vérification de la Qualité des Données")
    
    # Upload de fichier
    uploaded_file = st.file_uploader("Chargez un fichier CSV ou Excel", type=['csv', 'xls', 'xlsx'])
    
    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None:
            st.write("Aperçu des données chargées :")
            st.dataframe(df.head())

            # Sélection des options de validation
            st.sidebar.title("Options de Validation")
            
            freshness_check = st.sidebar.checkbox("Vérifier la fraîcheur des données")
            missing_check = st.sidebar.checkbox("Vérifier les données manquantes")
            postal_check = st.sidebar.checkbox("Valider les codes postaux")
            phone_check = st.sidebar.checkbox("Valider les numéros de téléphone")
            name_check = st.sidebar.checkbox("Valider les noms")
            continent_check = st.sidebar.checkbox("Valider les continents")
            country_check = st.sidebar.checkbox("Valider les pays")
            city_check = st.sidebar.checkbox("Valider les villes")
            email_check = st.sidebar.checkbox("Valider les emails")
            dob_check = st.sidebar.checkbox("Valider les dates de naissance")
            join_date_check = st.sidebar.checkbox("Valider les dates d'entrée en relation")
            address_check = st.sidebar.checkbox("Valider les adresses postales")
            
            # Lancer les validations choisies
            if freshness_check:
                date_column = st.sidebar.selectbox("Colonne des dates pour la fraîcheur", df.columns)
                if date_column in df.columns:
                    st.subheader("Analyse de la Fraîcheur")
                    freshness_report, obsolete_count = check_freshness(df, date_column)
                    st.write(f"Nombre d'enregistrements obsolètes : {obsolete_count}")
                    st.dataframe(freshness_report)

            if missing_check:
                required_columns = st.sidebar.multiselect("Colonnes requises pour les données", df.columns)
                if required_columns:
                    st.subheader("Analyse des Données Manquantes")
                    missing_report = check_missing_data(df, required_columns)
                    st.dataframe(missing_report)

            if postal_check:
                postal_code_column = st.sidebar.selectbox("Colonne des codes postaux", df.columns)
                if postal_code_column in df.columns:
                    st.subheader("Validation des Codes Postaux")
                    invalid_postal_df, invalid_count = validate_postal_code(df, postal_code_column)
                    st.write(f"Nombre de codes postaux invalides : {invalid_count}")
                    st.dataframe(invalid_postal_df)

            if phone_check:
                phone_column = st.sidebar.selectbox("Colonne des numéros de téléphone", df.columns)
                if phone_column in df.columns:
                    st.subheader("Validation des Numéros de Téléphone")
                    invalid_phone_df, invalid_count = validate_phone_number(df, phone_column)
                    st.write(f"Nombre de numéros de téléphone invalides : {invalid_count}")
                    st.dataframe(invalid_phone_df)

            if name_check:
                name_column = st.sidebar.selectbox("Colonne des noms", df.columns)
                if name_column in df.columns:
                    st.subheader("Validation des Noms")
                    invalid_name_df, invalid_count = validate_nom_prenom(df, name_column)
                    st.write(f"Nombre de noms invalides : {invalid_count}")
                    st.dataframe(invalid_name_df)

            if continent_check:
                continent_column = st.sidebar.selectbox("Colonne des continents", df.columns)
                if continent_column in df.columns:
                    st.subheader("Validation des Continents")
                    invalid_continent_df, invalid_count = validate_continent(df, continent_column)
                    st.write(f"Nombre de continents invalides : {invalid_count}")
                    st.dataframe(invalid_continent_df)

            if country_check:
                country_column = st.sidebar.selectbox("Colonne des pays", df.columns)
                if country_column in df.columns:
                    st.subheader("Validation des Pays")
                    invalid_country_df, invalid_count = validate_pays(df, country_column)
                    st.write(f"Nombre de pays invalides : {invalid_count}")
                    st.dataframe(invalid_country_df)

            if city_check:
                city_column = st.sidebar.selectbox("Colonne des villes", df.columns)
                if city_column in df.columns:
                    st.subheader("Validation des Villes")
                    invalid_city_df, invalid_count = validate_ville(df, city_column)
                    st.write(f"Nombre de villes invalides : {invalid_count}")
                    st.dataframe(invalid_city_df)

            if email_check:
                email_column = st.sidebar.selectbox("Colonne des emails", df.columns)
                if email_column in df.columns:
                    st.subheader("Validation des Emails")
                    invalid_email_df, invalid_count = validate_email(df, email_column)
                    st.write(f"Nombre d'emails invalides : {invalid_count}")
                    st.dataframe(invalid_email_df)

            if dob_check:
                dob_column = st.sidebar.selectbox("Colonne des dates de naissance", df.columns)
                if dob_column in df.columns:
                    st.subheader("Validation des Dates de Naissance")
                    invalid_dob_df, invalid_count = validate_date_naissance(df, dob_column)
                    st.write(f"Nombre de dates de naissance invalides : {invalid_count}")
                    st.dataframe(invalid_dob_df)

            if join_date_check:
                join_date_column = st.sidebar.selectbox("Colonne des dates d'entrée en relation", df.columns)
                if join_date_column in df.columns:
                    st.subheader("Validation des Dates d'Entrée en Relation")
                    invalid_join_date_df, invalid_count = validate_date_entree_relation(df, join_date_column)
                    st.write(f"Nombre de dates d'entrée invalides : {invalid_count}")
                    st.dataframe(invalid_join_date_df)

            if address_check:
                address_column = st.sidebar.selectbox("Colonne des adresses postales", df.columns)
                if address_column in df.columns:
                    st.subheader("Validation des Adresses Postales")
                    invalid_address_df, invalid_count = validate_adresse_postale(df, address_column)
                    st.write(f"Nombre d'adresses postales invalides : {invalid_count}")
                    st.dataframe(invalid_address_df)

# Lancer l'application Streamlit
if __name__ == "__main__":
    main()
