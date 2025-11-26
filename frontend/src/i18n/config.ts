/**
 * i18n Configuration for Aurora Life
 *
 * Internationalization setup using react-i18next
 * Supports multiple languages with automatic detection
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Translation resources
const resources = {
  en: {
    translation: {
      // Common
      common: {
        loading: 'Loading...',
        save: 'Save',
        cancel: 'Cancel',
        delete: 'Delete',
        edit: 'Edit',
        close: 'Close',
        back: 'Back',
        next: 'Next',
        submit: 'Submit',
        search: 'Search',
        filter: 'Filter',
        sort: 'Sort',
        error: 'Error',
        success: 'Success',
      },

      // Navigation
      nav: {
        dashboard: 'Dashboard',
        timeline: 'Timeline',
        analytics: 'Analytics',
        goals: 'Goals',
        settings: 'Settings',
        profile: 'Profile',
        logout: 'Logout',
      },

      // Dashboard
      dashboard: {
        welcome: 'Welcome back, {{name}}!',
        todayPredictions: "Today's Predictions",
        energyLevel: 'Energy Level',
        moodScore: 'Mood Score',
        recentActivity: 'Recent Activity',
        insights: 'Insights',
        quickActions: 'Quick Actions',
        addEvent: 'Add Event',
        viewAll: 'View All',
      },

      // Events
      events: {
        types: {
          sleep: 'Sleep',
          exercise: 'Exercise',
          work: 'Work',
          social: 'Social',
          mood: 'Mood',
          meal: 'Meal',
        },
        addEvent: 'Add Event',
        editEvent: 'Edit Event',
        deleteEvent: 'Delete Event',
        eventTime: 'Event Time',
        duration: 'Duration',
        notes: 'Notes',
        tags: 'Tags',
      },

      // Analytics
      analytics: {
        title: 'Analytics',
        timeRange: 'Time Range',
        last7Days: 'Last 7 Days',
        last30Days: 'Last 30 Days',
        last90Days: 'Last 90 Days',
        thisMonth: 'This Month',
        thisYear: 'This Year',
        custom: 'Custom',
        averageEnergy: 'Average Energy',
        averageMood: 'Average Mood',
        totalSleep: 'Total Sleep',
        totalExercise: 'Total Exercise',
        trends: 'Trends',
        patterns: 'Patterns',
      },

      // Goals
      goals: {
        title: 'Goals',
        create: 'Create Goal',
        active: 'Active Goals',
        completed: 'Completed Goals',
        progress: 'Progress',
        deadline: 'Deadline',
        category: 'Category',
        description: 'Description',
      },

      // Settings
      settings: {
        title: 'Settings',
        account: 'Account Settings',
        profile: 'Profile',
        privacy: 'Privacy',
        notifications: 'Notifications',
        integrations: 'Integrations',
        preferences: 'Preferences',
        language: 'Language',
        theme: 'Theme',
        timezone: 'Timezone',
      },

      // Onboarding
      onboarding: {
        welcome: 'Welcome to Aurora Life',
        step1: 'Tell us about yourself',
        step2: 'Set your goals',
        step3: 'Connect your apps',
        step4: 'Customize your experience',
        getStarted: 'Get Started',
        skip: 'Skip',
        finish: 'Finish Setup',
      },

      // Errors
      errors: {
        generic: 'Something went wrong',
        networkError: 'Network error. Please check your connection.',
        unauthorized: 'You are not authorized to perform this action',
        notFound: 'Resource not found',
        validationError: 'Please check your input',
      },

      // Auth
      auth: {
        login: 'Login',
        signup: 'Sign Up',
        logout: 'Logout',
        email: 'Email',
        password: 'Password',
        forgotPassword: 'Forgot Password?',
        resetPassword: 'Reset Password',
        confirmPassword: 'Confirm Password',
        signInWithGoogle: 'Sign in with Google',
        signInWithGitHub: 'Sign in with GitHub',
        noAccount: "Don't have an account?",
        haveAccount: 'Already have an account?',
      },
    },
  },

  es: {
    translation: {
      common: {
        loading: 'Cargando...',
        save: 'Guardar',
        cancel: 'Cancelar',
        delete: 'Eliminar',
        edit: 'Editar',
        close: 'Cerrar',
        back: 'Atrás',
        next: 'Siguiente',
        submit: 'Enviar',
        search: 'Buscar',
        filter: 'Filtrar',
        sort: 'Ordenar',
        error: 'Error',
        success: 'Éxito',
      },

      nav: {
        dashboard: 'Panel',
        timeline: 'Línea de Tiempo',
        analytics: 'Analíticas',
        goals: 'Objetivos',
        settings: 'Configuración',
        profile: 'Perfil',
        logout: 'Cerrar Sesión',
      },

      dashboard: {
        welcome: '¡Bienvenido de nuevo, {{name}}!',
        todayPredictions: 'Predicciones de Hoy',
        energyLevel: 'Nivel de Energía',
        moodScore: 'Puntuación de Ánimo',
        recentActivity: 'Actividad Reciente',
        insights: 'Perspectivas',
        quickActions: 'Acciones Rápidas',
        addEvent: 'Agregar Evento',
        viewAll: 'Ver Todo',
      },

      events: {
        types: {
          sleep: 'Sueño',
          exercise: 'Ejercicio',
          work: 'Trabajo',
          social: 'Social',
          mood: 'Ánimo',
          meal: 'Comida',
        },
        addEvent: 'Agregar Evento',
        editEvent: 'Editar Evento',
        deleteEvent: 'Eliminar Evento',
        eventTime: 'Hora del Evento',
        duration: 'Duración',
        notes: 'Notas',
        tags: 'Etiquetas',
      },

      auth: {
        login: 'Iniciar Sesión',
        signup: 'Registrarse',
        logout: 'Cerrar Sesión',
        email: 'Correo Electrónico',
        password: 'Contraseña',
        forgotPassword: '¿Olvidaste tu Contraseña?',
        resetPassword: 'Restablecer Contraseña',
        confirmPassword: 'Confirmar Contraseña',
        signInWithGoogle: 'Iniciar sesión con Google',
        signInWithGitHub: 'Iniciar sesión con GitHub',
        noAccount: '¿No tienes una cuenta?',
        haveAccount: '¿Ya tienes una cuenta?',
      },
    },
  },

  fr: {
    translation: {
      common: {
        loading: 'Chargement...',
        save: 'Enregistrer',
        cancel: 'Annuler',
        delete: 'Supprimer',
        edit: 'Modifier',
        close: 'Fermer',
        back: 'Retour',
        next: 'Suivant',
        submit: 'Soumettre',
        search: 'Rechercher',
        filter: 'Filtrer',
        sort: 'Trier',
        error: 'Erreur',
        success: 'Succès',
      },

      nav: {
        dashboard: 'Tableau de Bord',
        timeline: 'Chronologie',
        analytics: 'Analytiques',
        goals: 'Objectifs',
        settings: 'Paramètres',
        profile: 'Profil',
        logout: 'Déconnexion',
      },

      dashboard: {
        welcome: 'Bon retour, {{name}}!',
        todayPredictions: "Prédictions d'Aujourd'hui",
        energyLevel: "Niveau d'Énergie",
        moodScore: "Score d'Humeur",
        recentActivity: 'Activité Récente',
        insights: 'Perspectives',
        quickActions: 'Actions Rapides',
        addEvent: 'Ajouter un Événement',
        viewAll: 'Voir Tout',
      },

      events: {
        types: {
          sleep: 'Sommeil',
          exercise: 'Exercice',
          work: 'Travail',
          social: 'Social',
          mood: 'Humeur',
          meal: 'Repas',
        },
        addEvent: 'Ajouter un Événement',
        editEvent: 'Modifier un Événement',
        deleteEvent: 'Supprimer un Événement',
        eventTime: "Heure de l'Événement",
        duration: 'Durée',
        notes: 'Notes',
        tags: 'Tags',
      },

      auth: {
        login: 'Connexion',
        signup: "S'inscrire",
        logout: 'Déconnexion',
        email: 'Email',
        password: 'Mot de Passe',
        forgotPassword: 'Mot de passe oublié?',
        resetPassword: 'Réinitialiser le Mot de Passe',
        confirmPassword: 'Confirmer le Mot de Passe',
        signInWithGoogle: 'Se connecter avec Google',
        signInWithGitHub: 'Se connecter avec GitHub',
        noAccount: "Vous n'avez pas de compte?",
        haveAccount: 'Vous avez déjà un compte?',
      },
    },
  },

  de: {
    translation: {
      common: {
        loading: 'Laden...',
        save: 'Speichern',
        cancel: 'Abbrechen',
        delete: 'Löschen',
        edit: 'Bearbeiten',
        close: 'Schließen',
        back: 'Zurück',
        next: 'Weiter',
        submit: 'Absenden',
        search: 'Suchen',
        filter: 'Filtern',
        sort: 'Sortieren',
        error: 'Fehler',
        success: 'Erfolg',
      },

      nav: {
        dashboard: 'Dashboard',
        timeline: 'Zeitleiste',
        analytics: 'Analytik',
        goals: 'Ziele',
        settings: 'Einstellungen',
        profile: 'Profil',
        logout: 'Abmelden',
      },

      dashboard: {
        welcome: 'Willkommen zurück, {{name}}!',
        todayPredictions: 'Heutige Vorhersagen',
        energyLevel: 'Energielevel',
        moodScore: 'Stimmungswert',
        recentActivity: 'Letzte Aktivität',
        insights: 'Erkenntnisse',
        quickActions: 'Schnellaktionen',
        addEvent: 'Ereignis Hinzufügen',
        viewAll: 'Alle Anzeigen',
      },

      auth: {
        login: 'Anmelden',
        signup: 'Registrieren',
        logout: 'Abmelden',
        email: 'E-Mail',
        password: 'Passwort',
        forgotPassword: 'Passwort vergessen?',
        resetPassword: 'Passwort Zurücksetzen',
        confirmPassword: 'Passwort Bestätigen',
        signInWithGoogle: 'Mit Google anmelden',
        signInWithGitHub: 'Mit GitHub anmelden',
        noAccount: 'Noch kein Konto?',
        haveAccount: 'Bereits ein Konto?',
      },
    },
  },
};

// Initialize i18next
i18n
  .use(LanguageDetector) // Detect user language
  .use(initReactI18next) // Pass i18n instance to react-i18next
  .init({
    resources,
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',

    interpolation: {
      escapeValue: false, // React already escapes
    },

    detection: {
      // Order of language detection
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },
  });

export default i18n;
