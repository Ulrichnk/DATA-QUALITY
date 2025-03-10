import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from streamlit_option_menu import option_menu
from datetime import datetime
from expectation import Expectation, DataFrameContext  # Import de votre classe Expectation

# Configuration de la page
st.set_page_config(page_title="Quality Dashboard", layout="wide", initial_sidebar_state="expanded")

# ---- Barre latérale de navigation et chargement des données ----
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/6/6b/Pandas_logo.svg", width=100)
    selected = option_menu(
        menu_title="Navigation",
        options=["🏠 Accueil", "📊 Analyse Qualité", "Rapport Qualité"],
        icons=["house", "bar-chart", "gear"],
        menu_icon="cast",
        default_index=0,
    )

    # Sélection de la source des données
    data_source_type = st.radio("📂 Source des données :", ["Fichier CSV", "Base SQL"])

df = None
if data_source_type == "Fichier CSV":
    uploaded_file = st.sidebar.file_uploader("📥 Charger un fichier CSV", type=["csv", "xls", "xlsx"])
    if uploaded_file is not None:
        ext = uploaded_file.name.split('.')[-1].lower()
        try:
            if ext == "csv":
                df = pd.read_csv(uploaded_file)
            elif ext in ["xls", "xlsx"]:
                df = pd.read_excel(uploaded_file)
            st.sidebar.success("Fichier chargé avec succès.")
            st.sidebar.write("Aperçu des données :", df.head())
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
            st.stop()
    else:
        st.sidebar.warning("Veuillez charger un fichier CSV.")
        st.stop()

elif data_source_type == "Base SQL":
    db_url = st.sidebar.text_input("🔗 URL de la base de données :", "sqlite:///example.db")
    sql_query = st.sidebar.text_area("📝 Requête SQL :", "SELECT * FROM clients")
    if st.sidebar.button("🔍 Charger les données"):
        try:
            engine = create_engine(db_url)
            df = pd.read_sql(sql_query, engine)
            st.sidebar.success("Données chargées depuis la base SQL.")
            st.sidebar.write("Aperçu des données :")
            st.sidebar.dataframe(df.head())
        except Exception as e:
            st.sidebar.error(f"❌ Erreur de connexion : {e}")
            st.stop()
    else:
        st.sidebar.info("Entrez l'URL et la requête SQL puis cliquez sur le bouton.")
        st.stop()

# ---- Page Accueil ----
if selected == "🏠 Accueil":
    st.title("🏠 Accueil")

    # KPI Cards
    #col1, col2, col3, col4 = st.columns(4)
    col1, col4 = st.columns(2)

    with col1:
        st.metric(label="📈 Nombre d'enregistrements", value=df.shape[0])
    # with col2:
    #     #st.metric(label="✅ Taux de validité", value="95%", delta="↑ 2%")
    #     print("test")
    # with col3:
    #     #st.metric(label="❌ Taux d'erreurs", value="5%", delta="↓ 1%")
    #     print("test")
    with col4:
        st.metric(label="🕒 Dernière mise à jour", value=datetime.today().strftime("%Y-%m-%d"))

    # ---- Analyse Complémentaire des Données ----
    st.subheader("Analyse Complémentaire des Données")

    # 1. Fraîcheur de la donnée en années
    st.markdown("### Fraîcheur de la donnée")
    freshness_col = st.selectbox("Sélectionnez la colonne de date", options=df.columns.tolist(), key="freshness_analysis")
    threshold_years = st.number_input("Définir le seuil de mise à jour (en années)", min_value=0, value=1, step=1)
    freshness_ref = st.date_input("Choisir une date de référence", value=datetime.today(), key="ref_date")
    try:
        df[freshness_col] = pd.to_datetime(df[freshness_col], errors="coerce")
        ref_date = pd.to_datetime(freshness_ref)
        df["days_since_ref"] = (ref_date - df[freshness_col]).dt.days
        df["years_since_ref"] = df["days_since_ref"] / 365.0  # conversion approximative en années

        # KPI pour la fraîcheur
        avg_years = df["years_since_ref"].mean()
        median_years = df["years_since_ref"].median()
        std_years = df["years_since_ref"].std()
        col1, col2, col3 = st.columns(3)
        col1.metric("Moyenne (années)", f"{avg_years:.2f} ans")
        col2.metric("Médiane (années)", f"{median_years:.2f} ans")
        col3.metric("Écart-type (années)", f"{std_years:.2f} ans")

        # Histogramme de la distribution de la fraîcheur
        fig_hist = px.histogram(df, x="years_since_ref", nbins=30, title="Distribution de la fraîcheur des données (en années)")
        st.plotly_chart(fig_hist, use_container_width=True)

        # Graphique cumulatif de la fraîcheur
        df_sorted = df.sort_values("years_since_ref")
        df_sorted["cumulative"] = np.arange(1, df_sorted.shape[0] + 1) / df_sorted.shape[0]
        fig_line = px.line(df_sorted, x="years_since_ref", y="cumulative", 
                           title="Distribution cumulative de la fraîcheur des données")
        st.plotly_chart(fig_line, use_container_width=True)

        # Enregistrements nécessitant une mise à jour
        outdated_count = (df["years_since_ref"] > threshold_years).sum()
        total_records = df.shape[0]
        st.info(f"{outdated_count} enregistrements sur {total_records} nécessitent une mise à jour (plus de {threshold_years} ans).")
    except Exception as e:
        st.error(f"Erreur lors du calcul de la fraîcheur : {e}")

    st.write("---")

    # 2. Présence de la donnée
    st.markdown("### Présence de la donnée")
    missing_stats = df.isnull().mean() * 100
    missing_stats = missing_stats.sort_values(ascending=False)
    st.write("Pourcentage de valeurs manquantes par colonne :")
    fig_missing = px.bar(x=missing_stats.index, y=missing_stats.values,
                         labels={'x': 'Colonne', 'y': 'Pourcentage manquant (%)'},
                         title="Pourcentage de données manquantes par colonne")
    st.plotly_chart(fig_missing, use_container_width=True)

    missing_threshold = st.slider("Seuil pour identifier des enregistrements critiques (en % de données manquantes)",
                                  min_value=0.0, max_value=100.0, value=50.0)
    df["missing_percentage"] = df.isnull().mean(axis=1) * 100
    critical_records = df[df["missing_percentage"] >= missing_threshold]
    st.write(f"Nombre d'enregistrements avec au moins {missing_threshold}% de données manquantes : {critical_records.shape[0]}")
    if not critical_records.empty:
        with st.expander("Afficher les enregistrements critiques"):
            st.dataframe(critical_records)

    st.write("---")

    st.markdown("### Cohérence de la donnée : Codes Postaux")
    postal_cols = [col for col in df.columns if "postal" in col.lower() or "code" in col.lower()]
    if postal_cols:
        postal_col = st.selectbox("Sélectionnez la colonne des codes postaux", options=postal_cols, key="postal_code")
        
        validation_method = st.radio(
            "Méthode de validation des codes postaux",
            options=["Regex", "Fichier de codes valides", "Expectation (ensemble)"],
            key="postal_validation"
        )
        
        if validation_method == "Regex":
            regex_postal = st.text_input("Entrez la règle Regex pour les codes postaux", value=r"^\d{5}$", key="postal_regex")
            df["postal_valid"] = df[postal_col].astype(str).str.match(regex_postal)
            
        elif validation_method == "Fichier de codes valides":
            uploaded_postal_file = st.file_uploader("Chargez le fichier contenant les codes postaux valides", type=["csv", "xls", "xlsx", "txt"], key="postal_file")
            if uploaded_postal_file is not None:
                try:
                    if uploaded_postal_file.name.split('.')[-1].lower() in ["csv"]:
                        valid_postal_df = pd.read_csv(uploaded_postal_file)
                    elif uploaded_postal_file.name.split('.')[-1].lower() in ["xls", "xlsx"]:
                        valid_postal_df = pd.read_excel(uploaded_postal_file)
                    else:
                        valid_postal_df = pd.DataFrame([line.strip() for line in uploaded_postal_file.getvalue().decode("utf-8").splitlines()], columns=["code"])
                    valid_codes = set(valid_postal_df.iloc[:, 0].astype(str))
                    df["postal_valid"] = df[postal_col].astype(str).apply(lambda x: x in valid_codes)
                    st.success("Fichier de codes postaux chargé avec succès.")
                except Exception as e:
                    st.error(f"Erreur lors du chargement du fichier de codes postaux : {e}")
                    df["postal_valid"] = False
            else:
                st.info("Veuillez charger un fichier de codes postaux pour la validation ou choisissez une autre méthode.")
                df["postal_valid"] = False

        elif validation_method == "Expectation (ensemble)":
            # Utilisation de la logique de la fonction ExpectColumnValuesToBeInSet
            input_mode = st.radio(
                f"Source des valeurs autorisées pour {postal_col} (ExpectColumnValuesToBeInSet)",
                ["Saisie manuelle", "Téléchargement de fichier"],
                key=f"{postal_col}_ExpectColumnValuesToBeInSet_input_mode"
            )
            if input_mode == "Saisie manuelle":
                valid_values_str = st.text_input(
                    f"🔤 Valeurs autorisées pour {postal_col} (séparées par une virgule) :",
                    value="75000,69000,13000",
                    key=f"{postal_col}_ExpectColumnValuesToBeInSet_valid_values"
                )
                valid_values = [v.strip() for v in valid_values_str.split(",") if v.strip()]
            else:
                uploaded_file = st.file_uploader(
                    f"Télécharger un fichier CSV ou Excel contenant les valeurs autorisées pour {postal_col}",
                    type=["csv", "xlsx"],
                    key=f"{postal_col}_ExpectColumnValuesToBeInSet_file"
                )
                if uploaded_file is not None:
                    if uploaded_file.name.endswith("csv"):
                        df_valid_values = pd.read_csv(uploaded_file)
                    else:
                        df_valid_values = pd.read_excel(uploaded_file)
                    valid_values = df_valid_values.iloc[:, 0].tolist()
                else:
                    valid_values = None
                    st.warning("Veuillez télécharger un fichier CSV ou Excel valide pour continuer.")
                    
            if(valid_values is not None):
            
                # Application de l'Expectation pour vérifier que toutes les valeurs appartiennent à l'ensemble
                result = Expectation.ExpectColumnValuesToBeInSet(df, postal_col, valid_values)
                #st.write("Résultat de la vérification ExpectColumnValuesToBeInSet :", result)

                # Mise à jour de la colonne de validation
                df["postal_valid"] = df[postal_col].isin(valid_values)
        
        # Calcul des métriques de validation
        valid_count = df["postal_valid"].sum()
        invalid_count = df.shape[0] - valid_count
        st.metric("Taux de codes postaux valides", f"{(valid_count / df.shape[0]) * 100:.2f}%")
        
        if invalid_count > 0:
            st.warning(f"{invalid_count} codes postaux non conformes détectés.")
            with st.expander("Afficher les codes postaux non conformes"):
                st.dataframe(df.loc[df["postal_valid"] == False, [postal_col]])
        else:
            st.success("Tous les codes postaux respectent le format attendu.")

        fig_postal_pie = px.pie(
            names=["Valides", "Non valides"],
            values=[valid_count, invalid_count],
            title="Répartition des codes postaux"
        )
        st.plotly_chart(fig_postal_pie, use_container_width=True)

        fig_postal_bar = px.bar(
            x=["Valides", "Non valides"],
            y=[valid_count, invalid_count],
            labels={'x': 'Statut', 'y': 'Nombre'},
            title="Nombre de codes postaux valides vs non valides"
        )
        st.plotly_chart(fig_postal_bar, use_container_width=True)
    else:
        st.info("Aucune colonne de codes postaux détectée dans les données.")

#--------------------------------------------------------------------------
    st.write("---")

    # 4. Suggestions d'imputation pour les valeurs manquantes
    st.markdown("### Suggestions d'imputation")
    impute_choice = st.selectbox("Choisissez une méthode d'imputation", options=["Aucune", "Moyenne", "Médiane", "Mode", "Suppression"])
    if impute_choice != "Aucune":
        imputed_df = df.copy()
        if impute_choice in ["Moyenne", "Médiane"]:
            for col in imputed_df.select_dtypes(include=np.number).columns:
                if impute_choice == "Moyenne":
                    imputed_df[col].fillna(imputed_df[col].mean(), inplace=True)
                else:
                    imputed_df[col].fillna(imputed_df[col].median(), inplace=True)
        elif impute_choice == "Mode":
            for col in imputed_df.columns:
                try:
                    imputed_df[col].fillna(imputed_df[col].mode()[0], inplace=True)
                except Exception as e:
                    st.error(f"Erreur lors de l'imputation par le mode pour la colonne {col} : {e}")
        elif impute_choice == "Suppression":
            imputed_df = imputed_df.dropna()
        st.success(f"Imputation réalisée avec la méthode : {impute_choice}")
        with st.expander("Aperçu des données après imputation"):
            st.dataframe(imputed_df.head())

# ---- Page Analyse Qualité ----
elif selected == "📊 Analyse Qualité":
    st.title("📊 Analyse de la Qualité des Données")

    # Création d'un onglet pour la vérification par Expectation
    tab_expect=True
    if(tab_expect):
        st.subheader("Vérification des règles de qualité avec Expectation")
        functions = [
            "ExpectColumnValuesToNotBeNull",
            "ExpectColumnValuesToBeBetween",
            "ExpectColumnValuesToMatchRegex",
            "ExpectColumnValuesToBeUnique",
            "ExpectColumnValuesToBeWithinIQR",
            "ExpectColumnValuesToBeInSet",
            "ExpectColumnValuesToHaveLengthBetween",
            "ExpectColumnValuesToRespectOrder",
            "ExpectColumnValuesToBeInDateRange",
            "ExpectRowCompletenessToBeAboveThreshold"
        ]
        function_choice = st.selectbox("📌 Choisissez une fonction de vérification :", functions)
        params = {}

        if function_choice in [
            "ExpectColumnValuesToNotBeNull",
            "ExpectColumnValuesToBeBetween",
            "ExpectColumnValuesToMatchRegex",
            "ExpectColumnValuesToBeUnique",
            "ExpectColumnValuesToBeWithinIQR",
            "ExpectColumnValuesToBeInSet",
            "ExpectColumnValuesToHaveLengthBetween",
            "ExpectColumnValuesToBeInDateRange"
        ]:
            col_selected = st.selectbox("Sélectionnez une colonne :", df.columns.tolist())
            params["column"] = col_selected

        if function_choice == "ExpectColumnValuesToRespectOrder":
            col1 = st.selectbox("Sélectionnez la première colonne :", df.columns.tolist(), key="col1_order")
            col2 = st.selectbox("Sélectionnez la seconde colonne :", df.columns.tolist(), key="col2_order")
            params["column1"] = col1
            params["column2"] = col2

        if function_choice == "ExpectColumnValuesToBeBetween":
            params["min_value"] = st.number_input("🔢 Valeur minimale :", value=0.0)
            params["max_value"] = st.number_input("🔢 Valeur maximale :", value=100.0)

        if function_choice == "ExpectColumnValuesToMatchRegex":
            params["regex"] = st.text_input("🔤 Regex :", value=r"^[\w\.-]+@[\w\.-]+\.\w+$")

        if function_choice == "ExpectColumnValuesToBeWithinIQR":
            params["factor"] = st.number_input("🔢 Facteur (par défaut 1.5) :", value=1.5)

        if function_choice == "ExpectColumnValuesToBeInSet":
            input_mode = st.radio("Sélectionnez la source des valeurs autorisées :", ["Saisie manuelle", "Téléchargement de fichier"])
            if input_mode == "Saisie manuelle":
                valid_values_str = st.text_input("🔤 Valeurs autorisées (séparées par une virgule) :", value="A,B,C")
                params["valid_values"] = [v.strip() for v in valid_values_str.split(",") if v.strip()]
            else:
                uploaded_file = st.file_uploader("Télécharger un fichier CSV ou Excel contenant les valeurs autorisées", type=["csv", "xlsx"])
                if uploaded_file is not None:
                    if uploaded_file.name.endswith("csv"):
                        df_valid_values = pd.read_csv(uploaded_file)
                    else:
                        df_valid_values = pd.read_excel(uploaded_file)
                    params["valid_values"] = df_valid_values.iloc[:, 0].tolist()
                else:
                    st.warning("Veuillez télécharger un fichier CSV ou Excel valide pour continuer.")

        if function_choice == "ExpectColumnValuesToHaveLengthBetween":
            params["min_length"] = st.number_input("🔢 Longueur minimale :", value=1, step=1)
            params["max_length"] = st.number_input("🔢 Longueur maximale :", value=100, step=1)

        if function_choice == "ExpectColumnValuesToBeInDateRange":
            params["min_date"] = st.date_input("📅 Date minimale :", value=datetime(2000, 1, 1))
            params["max_date"] = st.date_input("📅 Date maximale :", value=datetime.today())

        if function_choice == "ExpectRowCompletenessToBeAboveThreshold":
            params["threshold"] = st.slider("🔢 Seuil de complétude par ligne :", min_value=0.0, max_value=1.0, value=0.8)

        if st.button("🚀 Lancer la vérification"):
            with DataFrameContext(df) as ctx:
                func = getattr(Expectation, function_choice)
                try:
                    ctx.apply_expectation(func, **params)
                except Exception as e:
                    st.error(f"Erreur lors de l'exécution de {function_choice} : {e}")
            quality_report = pd.DataFrame(ctx.reports)
            st.write("### Rapport de validation")
            st.dataframe(quality_report)

            if not quality_report.empty:
                # Calcul global du pourcentage d'erreur (unexpected)
                total_elements = quality_report['element_count'].sum()
                total_unexpected = quality_report['unexpected_count'].sum()
                overall_unexpected_pct = round((total_unexpected / total_elements) * 100, 2) if total_elements > 0 else 0
                overall_conform_pct = round(100 - overall_unexpected_pct, 2)
                
                df_percentages = pd.DataFrame({
                    'Statut': ['Erreurs', 'Conformes'],
                    'Pourcentage': [overall_unexpected_pct, overall_conform_pct]
                })
                
                fig_pie = px.pie(
                    df_percentages, 
                    names='Statut', 
                    values='Pourcentage',
                    title="Répartition globale des tests",
                    color='Statut', 
                    color_discrete_map={'Erreurs': 'red', 'Conformes': 'green'},
                    hover_data=['Pourcentage']
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

                st.write("### Détails des erreurs détectées")
                for _, row in quality_report.iterrows():
                    if not row["success"]:
                        with st.expander(f"🚨 {row['check']}"):
                            st.write(f"**Nombre total d'éléments analysés** : {row['element_count']}")
                            st.write(f"**Nombre d'erreurs détectées** : {row['unexpected_count']} ({row['unexpected_percent']}%)")
                            st.write(f"**Valeurs problématiques** : {row['unexpected_list']}")
                if quality_report["unexpected_count"].sum() == 0:
                    st.success("✅ Aucune anomalie détectée !")
                    
elif selected == "Rapport Qualité":
    st.title("Analyse Qualité - Vérifications Personnalisées")
    tab_config, tab_results = st.tabs(["Configuration des Vérifications", "Résultats des Vérifications"])
    
    with tab_config:
        st.header("Configuration par colonne")
        st.write("Pour chaque colonne, sélectionnez les fonctions de vérification à appliquer ainsi que leurs paramètres (le cas échéant).")
        available_functions = [
            "ExpectColumnValuesToNotBeNull",
            "ExpectColumnValuesToBeBetween",
            "ExpectColumnValuesToMatchRegex",
            "ExpectColumnValuesToBeUnique",
            "ExpectColumnValuesToBeWithinIQR",
            "ExpectColumnValuesToBeInSet",
            "ExpectColumnValuesToHaveLengthBetween",
            "ExpectColumnValuesToRespectOrder",
            "ExpectColumnValuesToBeInDateRange"
        ]
        custom_config = {}
        for col in df.columns:
            with st.expander(f"Configuration pour la colonne **{col}**", expanded=False):
                selected_funcs = st.multiselect(f"Fonctions à appliquer sur {col} :", available_functions, key=f"func_{col}")
                if selected_funcs:
                    custom_config[col] = {}
                    for func in selected_funcs:
                        if func == "ExpectColumnValuesToBeBetween":
                            min_val = st.number_input(f"Valeur minimale pour {col} ({func})", value=0.0, key=f"{col}_{func}_min")
                            max_val = st.number_input(f"Valeur maximale pour {col} ({func})", value=100.0, key=f"{col}_{func}_max")
                            custom_config[col][func] = {"min_value": min_val, "max_value": max_val}
                        elif func == "ExpectColumnValuesToMatchRegex":
                            regex = st.text_input(f"Regex pour {col} ({func})", value=r"^[\w\.-]+@[\w\.-]+\.\w+$", key=f"{col}_{func}_regex")
                            custom_config[col][func] = {"regex": regex}
                        elif func == "ExpectColumnValuesToBeWithinIQR":
                            factor = st.number_input(f"Facteur pour {col} ({func})", value=1.5, key=f"{col}_{func}_factor")
                            custom_config[col][func] = {"factor": factor}
                        elif func == "ExpectColumnValuesToBeInSet":
                            input_mode = st.radio(f"Source des valeurs autorisées pour {col} ({func})", 
                                                   ["Saisie manuelle", "Téléchargement de fichier"], key=f"{col}_{func}_input_mode")
                            if input_mode == "Saisie manuelle":
                                valid_values_str = st.text_input(f"🔤 Valeurs autorisées pour {col} (séparées par une virgule) :", 
                                                                 value="A,B,C", key=f"{col}_{func}_valid_values")
                                valid_values = [v.strip() for v in valid_values_str.split(",") if v.strip()]
                            else:
                                uploaded_file = st.file_uploader(f"Télécharger un fichier CSV ou Excel contenant les valeurs autorisées pour {col}", 
                                                                 type=["csv", "xlsx"], key=f"{col}_{func}_file")
                                if uploaded_file is not None:
                                    if uploaded_file.name.endswith("csv"):
                                        df_valid_values = pd.read_csv(uploaded_file)
                                    else:
                                        df_valid_values = pd.read_excel(uploaded_file)
                                    valid_values = df_valid_values.iloc[:, 0].tolist()
                                else:
                                    valid_values = None
                                    st.warning("Veuillez télécharger un fichier CSV ou Excel valide pour continuer.")
                            custom_config[col][func] = {"valid_values": valid_values}
                        elif func == "ExpectColumnValuesToHaveLengthBetween":
                            min_length = st.number_input(f"Longueur minimale pour {col} ({func})", value=1, step=1, key=f"{col}_{func}_min_length")
                            max_length = st.number_input(f"Longueur maximale pour {col} ({func})", value=100, step=1, key=f"{col}_{func}_max_length")
                            custom_config[col][func] = {"min_length": int(min_length), "max_length": int(max_length)}
                        elif func == "ExpectColumnValuesToRespectOrder":
                            other_cols = [c for c in df.columns if c != col]
                            if other_cols:
                                col2 = st.selectbox(f"Sélectionnez la seconde colonne pour {col} ({func})", other_cols, key=f"{col}_{func}_col2")
                                custom_config[col][func] = {"column2": col2}
                            else:
                                st.error("Pas assez de colonnes pour configurer cette vérification.")
                        elif func == "ExpectColumnValuesToBeInDateRange":
                            min_date = st.date_input(f"Date minimale pour {col} ({func})", value=datetime(2000, 1, 1), key=f"{col}_{func}_min_date")
                            max_date = st.date_input(f"Date maximale pour {col} ({func})", value=datetime.today(), key=f"{col}_{func}_max_date")
                            custom_config[col][func] = {"min_date": pd.to_datetime(min_date), "max_date": pd.to_datetime(max_date)}
                        else:
                            custom_config[col][func] = {}
        st.session_state.custom_config = custom_config
        if st.button("Valider les vérifications"):
            results = []
            for col, funcs in custom_config.items():
                for func_name, params in funcs.items():
                    try:
                        result = getattr(Expectation, func_name)(df, col, **params)
                        results.append(result)
                    except Exception as e:
                        results.append({
                            "check": f"{func_name}({col})",
                            "element_count": None,
                            "unexpected_count": None,
                            "unexpected_percent": None,
                            "unexpected_list": str(e),
                            "success": False
                        })
            st.session_state.results = results
            st.success("Vérifications effectuées. Consultez l'onglet Résultats.")

    with tab_results:
        st.header("Résultats des vérifications")
        if "results" in st.session_state:
            results = st.session_state.results
            results_df = pd.DataFrame(results)
            results_df["unexpected_list"] = results_df["unexpected_list"].apply(
                lambda x: ", ".join(map(str, x)) if isinstance(x, list) else str(x)
            )
            st.dataframe(results_df)
            st.subheader("Métriques")
            st.markdown("""
            <style>
            div[data-testid="stMetricValue"] {
                font-size: 28px;
                font-weight: bold;
                color: #FF4136;
            }
            div[data-testid="stMetricLabel"] {
                font-size: 18px;
                color: #333;
            }
            [data-testid="stMetric"] {
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 8px;
                margin: 5px;
            }
            </style>
            """, unsafe_allow_html=True)
            cols = st.columns(3)
            for idx, res in enumerate(results):
                if res["unexpected_percent"] is not None:
                    cols[idx % 3].metric(label=res["check"], value=f"{res['unexpected_percent']}%")
        else:
            st.info("Aucune vérification n'a été effectuée pour le moment. Configurez et validez dans l'onglet Configuration.")
