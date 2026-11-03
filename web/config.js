// Configuración de AstroVital (se carga antes que index.html).
// Déjalo vacío para correr en MODO DEMO (datos simulados, teclas 1/2/3/0).
// Para el modo EN VIVO, pega aquí los datos de tu proyecto en Supabase
// (Project Settings -> API). Usa SOLO la clave "anon public", nunca la service_role.
window.ASTROVITAL = {
  SUPABASE_URL: "https://mjjdncqbloyuprugzuds.supabase.co",
  SUPABASE_ANON_KEY: "sb_publishable_TFahFkgBY-SsJm5GKwomAQ_FAa68atv",
  TABLA: "lecturas",
  INTERVALO_MS: 1000
};