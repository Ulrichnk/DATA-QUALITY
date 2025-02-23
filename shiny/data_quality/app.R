# Chargement des bibliothèques nécessaires
library(shiny)
library(DT)
library(ggplot2)
library(dplyr)
library(tidyr)
library(lubridate)
library(plotly)
library(janitor)
library(skimr)
library(readxl)
library(shinydashboard)
library(reshape2)  # Pour la transformation au format long (boxplot)

# Fonction pour charger les données (les données manquantes sont conservées)
data_loader <- function(file) {
  ext <- tools::file_ext(file$datapath)
  if (ext == "csv") {
    df <- read.csv(file$datapath, stringsAsFactors = FALSE)
  } else if (ext %in% c("xls", "xlsx")) {
    df <- read_excel(file$datapath)
  } else {
    stop("Format de fichier non supporté")
  }
  return(df)
}

# Interface utilisateur
ui <- dashboardPage(
  dashboardHeader(title = "Contrôle Qualité des Données"),
  dashboardSidebar(
    fileInput("file", "Choisir un fichier (CSV ou Excel)", 
              accept = c(".csv", ".xls", ".xlsx")),
    
    # Analyse des valeurs manquantes
    h4("Analyse des valeurs manquantes"),
    selectInput("missing_cols", "Sélectionner les colonnes", choices = NULL, multiple = TRUE),
    actionButton("validate_missing", "Valider"),
    
    # Analyse de la fraîcheur
    h4("Analyse de la fraîcheur"),
    selectInput("freshness_col", "Sélectionner la colonne date", choices = NULL),
    dateInput("freshness_ref", "Choisir une date de référence", value = Sys.Date()),
    actionButton("validate_freshness", "Valider"),
    
    # Analyse générale
    h4("Analyse des données"),
    selectInput("analysis_cols", "Sélectionner les colonnes", choices = NULL, multiple = TRUE),
    actionButton("validate_analysis", "Valider"),
    
    # Vérification de la cohérence des données
    h4("Cohérence des données"),
    selectInput("coherence_col", "Sélectionner une colonne", choices = NULL),
    selectInput("validation_func", "Choisir une fonction de validation", 
                choices = c("Validation 1", "Validation 2", "Validation 3")),
    actionButton("validate_coherence", "Valider")
  ),
  dashboardBody(
    tabsetPanel(
      tabPanel("Affichage des Données",
               fluidRow(
                 valueBoxOutput("missing_percentage", width = 6),
                 valueBoxOutput("duplicate_percentage", width = 6)
               ),
               # Card : Aperçu des données chargées
               fluidRow(
                 box(title = "Données Chargées", status = "primary", solidHeader = TRUE, width = 12, collapsible = TRUE,
                     DTOutput("data_preview"))
               ),
               # Cards supplémentaires : Dimensions et Types des Variables
               fluidRow(
                 box(title = "Dimensions des Données", status = "info", solidHeader = TRUE, width = 6,
                     uiOutput("data_dimensions")),
                 box(title = "Types des Variables", status = "warning", solidHeader = TRUE, width = 6,
                     DTOutput("variable_types"))
               )
      ),
      tabPanel("Analyse des Données",
               fluidRow(
                 box(title = "Résumé des Données", status = "primary", solidHeader = TRUE, width = 6, collapsible = TRUE,
                     DTOutput("summary")),
                 box(title = "Valeurs Manquantes", status = "warning", solidHeader = TRUE, width = 6, collapsible = TRUE,
                     DTOutput("missing_counts"))
               ),
               fluidRow(
                 box(title = "Fraîcheur des Données", status = "success", solidHeader = TRUE, width = 6, collapsible = TRUE,
                     DTOutput("data_freshness")),
                 box(title = "Cohérence des Données", status = "info", solidHeader = TRUE, width = 6, collapsible = TRUE,
                     DTOutput("coherence_results"))
               )
      ),
      tabPanel("Visualisation Graphique",
               # Card de configuration graphique
               fluidRow(
                 box(title = "Configuration du Graphique", status = "primary", solidHeader = TRUE, width = 12, collapsible = TRUE,
                     selectInput("graph_type", "Choisir un type de graphique", 
                                 choices = c("Histogramme", "Boxplot", "Camembert")),
                     selectizeInput("graph_col", "Sélectionner la ou les colonnes", 
                                    choices = NULL, multiple = TRUE, 
                                    options = list(placeholder = 'Sélectionnez des colonnes...')),
                     actionButton("plot_graph", "Tracer le graphique")
                 )
               ),
               # Card d'affichage du graphique généré
               fluidRow(
                 box(title = "Graphique généré", status = "success", solidHeader = TRUE, width = 12, collapsible = TRUE,
                     plotlyOutput("graph_output"))
               )
      )
    )
  )
)

# Serveur
server <- function(input, output, session) {
  data <- reactiveVal(NULL)
  # Variable réactive pour stocker la sélection des colonnes
  selectedCols <- reactiveVal(NULL)
  
  # Chargement des données et mise à jour dynamique des sélecteurs
  observeEvent(input$file, {
    tryCatch({
      df <- data_loader(input$file)
      data(df)
      updateSelectInput(session, "missing_cols", choices = names(df))
      updateSelectInput(session, "freshness_col", choices = names(df))
      updateSelectInput(session, "analysis_cols", choices = names(df))
      updateSelectInput(session, "coherence_col", choices = names(df))
      # On met à jour le selectizeInput en conservant éventuellement la sélection précédente
      currentSelection <- isolate(selectedCols())
      updateSelectizeInput(session, "graph_col", choices = names(df), selected = currentSelection)
    }, error = function(e) {
      showModal(modalDialog(
        title = "Erreur",
        paste("Erreur lors du chargement du fichier :", e$message),
        easyClose = TRUE,
        footer = NULL
      ))
    })
  })
  
  # Card : Dimensions des données
  output$data_dimensions <- renderUI({
    req(data())
    df <- data()
    n_rows <- nrow(df)
    n_cols <- ncol(df)
    HTML(paste("<b>Nombre de lignes :</b>", n_rows, "<br><b>Nombre de colonnes :</b>", n_cols))
  })
  
  # Card : Types des variables
  output$variable_types <- renderDT({
    req(data())
    df <- data()
    dt <- data.frame(Variable = names(df), Type = sapply(df, class))
    datatable(dt, options = list(dom = 't', paging = FALSE))
  })
  
  # Visualisation graphique
  observeEvent(input$plot_graph, {
    req(data(), input$graph_type, input$graph_col)
    # Stockage de la sélection actuelle dans la variable réactive
    selectedCols(input$graph_col)
    
    df <- data()
    plots <- list()  # Liste pour stocker les graphiques générés
    
    if (input$graph_type == "Histogramme") {
      # Pour chaque colonne sélectionnée, générer un histogramme
      for (col in selectedCols()) {
        p <- ggplot(df, aes(x = .data[[col]])) +
          geom_histogram(fill = "blue", bins = 30, na.rm = TRUE) +
          labs(title = paste("Histogramme de", col), x = col, y = "Fréquence") +
          theme_minimal()
        plots[[col]] <- ggplotly(p)
      }
      
    } else if (input$graph_type == "Boxplot") {
      if (length(selectedCols()) == 1) {
        # Boxplot simple pour une seule colonne
        col <- selectedCols()[1]
        p <- ggplot(df, aes(y = .data[[col]])) +
          geom_boxplot(fill = "red", na.rm = TRUE) +
          labs(title = paste("Boxplot de", col), y = col) +
          theme_minimal()
        plots[[col]] <- ggplotly(p)
      } else {
        # Pour plusieurs colonnes, transformation du jeu de données au format long
        df_long <- pivot_longer(df, cols = all_of(selectedCols()), 
                                names_to = "variable", values_to = "value")
        p <- ggplot(df_long, aes(x = variable, y = value)) +
          geom_boxplot(fill = "red", na.rm = TRUE) +
          labs(title = "Boxplot", x = "", y = "Valeur") +
          theme_minimal()
        plots[["Boxplot_combiné"]] <- ggplotly(p)
      }
      
    } else if (input$graph_type == "Camembert") {
      # Pour chaque colonne, générer un camembert (pie chart)
      for (col in selectedCols()) {
        df_count <- df %>%
          filter(!is.na(.data[[col]])) %>%
          count(!!sym(col)) %>%
          rename(Freq = n)
        p <- ggplot(df_count, aes(x = "", y = Freq, fill = factor(!!sym(col)))) +
          geom_bar(stat = "identity", width = 1) +
          coord_polar(theta = "y") +
          labs(title = paste("Camembert de", col), fill = col) +
          theme_void()
        plots[[col]] <- ggplotly(p)
      }
    }
    
    # Affichage : s'il n'y a qu'un seul graphique, l'afficher directement,
    # sinon les arranger en grille via subplot
    if (length(plots) == 1) {
      output$graph_output <- renderPlotly({ plots[[1]] })
    } else {
      nrows <- ceiling(length(plots) / 2)
      output$graph_output <- renderPlotly({ subplot(plots, nrows = nrows, margin = 0.05) })
    }
  })
  
  # Calcul et affichage du pourcentage de valeurs manquantes
  output$missing_percentage <- renderValueBox({
    req(data())
    df <- data()
    missing_percent <- mean(sapply(df, function(col) sum(is.na(col)) / length(col))) * 100
    valueBox(
      paste0(round(missing_percent, 2), "%"), "Valeurs Manquantes", 
      icon = icon("exclamation-triangle"), color = "yellow"
    )
  })
  
  # Calcul et affichage du pourcentage de doublons
  output$duplicate_percentage <- renderValueBox({
    req(data())
    df <- data()
    duplicate_percent <- (nrow(df) - nrow(distinct(df))) / nrow(df) * 100
    valueBox(
      paste0(round(duplicate_percent, 2), "%"), "Doublons", 
      icon = icon("copy"), color = "red"
    )
  })
  
  # Aperçu des données
  output$data_preview <- renderDT({
    req(data())
    datatable(data(), options = list(pageLength = 5))
  })
  
  # Résumé des données avec skimr
  output$summary <- renderDT({
    req(data(), input$analysis_cols)
    df <- data() %>% select(all_of(input$analysis_cols))
    skim(df) %>% DT::datatable(options = list(pageLength = 5))
  })
  
  # Comptage des valeurs manquantes par colonne
  output$missing_counts <- renderDT({
    req(data(), input$missing_cols)
    df <- data() %>% select(all_of(input$missing_cols))
    missing_counts <- sapply(df, function(col) sum(is.na(col)))
    datatable(missing_counts, options = list(pageLength = 5))
  })
  
  # Analyse de la fraîcheur des données
  output$data_freshness <- renderDT({
    req(data(), input$freshness_col, input$freshness_ref)
    df <- data()
    freshness_col <- input$freshness_col
    freshness_ref <- input$freshness_ref
    df <- df %>% 
      mutate(days_since_ref = as.numeric(difftime(ymd(freshness_ref), ymd(.data[[freshness_col]]), units = "days")))
    datatable(df %>% select(all_of(freshness_col), days_since_ref), options = list(pageLength = 5))
  })
  
  # Vérification de la cohérence des données (exemple de validation)
  output$coherence_results <- renderDT({
    req(data(), input$coherence_col, input$validation_func)
    df <- data()
    col <- input$coherence_col
    validation_func <- input$validation_func
    
    if (validation_func == "Validation 1") {
      result <- df %>% summarise(validation_result = "Validation 1 Result")
    } else if (validation_func == "Validation 2") {
      result <- df %>% summarise(validation_result = "Validation 2 Result")
    } else if (validation_func == "Validation 3") {
      result <- df %>% summarise(validation_result = "Validation 3 Result")
    }
    
    datatable(result, options = list(pageLength = 5))
  })
}

# Lancement de l'application
shinyApp(ui = ui, server = server)
