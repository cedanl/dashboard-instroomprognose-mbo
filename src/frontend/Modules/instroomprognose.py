# Install required dependencies:
# $ uv sync
# Or if using pip:
# $ pip install plotly

import re
from datetime import datetime
import streamlit as st
import pandas as pd

try:
    import plotly.graph_objects as go
except ImportError:
    st.error("❌ Plotly is niet geïnstalleerd. Installeer het met: `uv sync` of `pip install plotly`")
    st.stop()

# Import utility functions from the Files module
import os
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
file_module_path = os.path.join(current_dir, '..', 'Bestanden', 'selecteer_bestandslocatie.py')
file_module_path = os.path.abspath(file_module_path)

try:
    spec = importlib.util.spec_from_file_location("selecteer_bestandslocatie", file_module_path)
    file_module = importlib.util.module_from_spec(spec)
    file_module.__dict__['_imported_via_importlib'] = True
    spec.loader.exec_module(file_module)
    
    get_prognose_files = getattr(file_module, 'get_prognose_files', None)
    get_beschrijving_files = getattr(file_module, 'get_beschrijving_files', None)
    read_data_file = getattr(file_module, 'read_data_file', None)
    read_excel_file = getattr(file_module, 'read_excel_file', None)
    
    if get_beschrijving_files is None:
        get_uploaded_files = getattr(file_module, 'get_uploaded_files', None)
        get_beschrijving_files = (lambda: get_uploaded_files('beschrijving')) if get_uploaded_files else (lambda: [])
    if get_prognose_files is None:
        get_uploaded_files = getattr(file_module, 'get_uploaded_files', None)
        if get_uploaded_files is not None:
            def get_prognose_files():
                return get_uploaded_files('prognose')
        else:
            raise AttributeError("get_uploaded_files not found in module")
    
    if read_excel_file is None:
        read_excel_file = read_data_file
        
except Exception as e:
    st.error(f"Kon bestandsfuncties niet laden: {str(e)}")
    st.stop()


def find_column(df, possible_names):
    """Find column name from possible variations (case-insensitive)"""
    df_cols_lower = {col.lower(): col for col in df.columns}
    for name in possible_names:
        if name.lower() in df_cols_lower:
            return df_cols_lower[name.lower()]
    return None


def is_inschrijvingen_summary(filename):
    """Check if filename matches inschrijvingen_summary_* pattern"""
    name_lower = filename.lower()
    return name_lower.startswith('inschrijvingen_summary') and (name_lower.endswith('.csv') or name_lower.endswith('.xlsx') or name_lower.endswith('.xls'))


def parse_prediction_mbo_filename(filename):
    """
    Parse predictions_mbo_****_week## filename.
    **** = jaartal, ## = weeknummer. Returns (jaar, week) or None if no match.
    """
    match = re.match(r'predictions_mbo_(\d+)_week(\d+)\.', filename, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def is_prediction_mbo(filename):
    """Check if filename matches predictions_mbo_****_week## pattern"""
    return parse_prediction_mbo_filename(filename) is not None


def is_application_enriched(filename):
    """Check if filename matches application(s)_enriched_with_context_* pattern"""
    name_lower = filename.lower()
    return (
        (name_lower.startswith('application_enriched_with_context') or name_lower.startswith('applications_enriched_with_context')) and
        (name_lower.endswith('.csv') or name_lower.endswith('.xlsx') or name_lower.endswith('.xls'))
    )


def get_week_of_october_1st(year):
    """Return ISO week number for October 1st of the given year."""
    return datetime(year, 10, 1).isocalendar()[1]


def sort_weeks_with_oct1_first(weeks, year):
    """Sort week numbers so the week containing October 1st comes first."""
    oct1_week = get_week_of_october_1st(year)
    # Create ordering: weeks >= oct1_week first (ascending), then weeks < oct1_week (ascending)
    def week_order(w):
        if w >= oct1_week:
            return (0, w)
        return (1, w)
    return sorted(weeks, key=week_order)


def get_best_week_for_oct1(available_weeks, year):
    """
    Return the best week for '1 oktober' data: de week waarin 1 oktober valt,
    of anders de week ervoor die daar het dichtste bij in de buurt komt.
    """
    oct1_week = get_week_of_october_1st(year)
    if oct1_week in available_weeks:
        return oct1_week
    # Zoek weken vóór oct1_week (dichtstbijzijnde ervoor)
    weeks_before = [w for w in available_weeks if w < oct1_week]
    if weeks_before:
        return max(weeks_before)
    # Geen week ervoor: neem de vroegste beschikbare week
    return min(available_weeks) if available_weeks else None


def _schooljaar_matches_target(val, target_jaar):
    """Check of schooljaar overeenkomt met target (2024, '2024-2025', '2023-2024' etc)."""
    if pd.isna(val):
        return False
    s = str(val).strip()
    if '-' in s:
        try:
            start_jaar = int(s.split('-')[0])
            end_jaar = int(s.split('-')[-1])
            return start_jaar == target_jaar or end_jaar == target_jaar
        except (ValueError, IndexError):
            pass
    try:
        return int(float(val)) == target_jaar
    except (ValueError, TypeError):
        return False


def get_weekly_ingeschreven(df_app, target_jaar, bsn_col, week_col, jaar_col, status_col, inst_col, lw_col, opl_col):
    """
    Build dict week -> aantal unieke studenten (bsn_hash) uit application_enriched.
    Alleen rijen met status = ENROLLED. Kolommen: bsn_hash, week_of_year, schooljaar_afgeleid.
    """
    if df_app is None or df_app.empty or not bsn_col or not week_col or not jaar_col or not status_col:
        return {}
    df = df_app.copy()
    # Alleen status = ENROLLED
    df = df[df[status_col].astype(str).str.upper().str.strip() == 'ENROLLED']
    # Filter op jaar (schooljaar_afgeleid: 2024, 2024-2025 of 2023-2024)
    df = df[df[jaar_col].apply(lambda v: _schooljaar_matches_target(v, target_jaar))]
    # Filters toepassen
    if inst_col and inst_col in df.columns and selected_instelling:
        df = df[df[inst_col].astype(str).isin(selected_instelling)]
    if lw_col and lw_col in df.columns and selected_leerweg:
        df = df[df[lw_col].astype(str).isin(selected_leerweg)]
    if opl_col and opl_col in df.columns and selected_opleiding:
        df = df[df[opl_col].astype(str).isin(selected_opleiding)]
    if df.empty:
        return {}
    # Week als integer
    df['_week'] = pd.to_numeric(df[week_col], errors='coerce')
    df = df[df['_week'].notna() & (df['_week'] >= 1) & (df['_week'] <= 53)]
    df['_week'] = df['_week'].astype(int)
    # Tel unieke bsn_hash per week
    return df.groupby('_week')[bsn_col].nunique().to_dict()


# Ingeschreven jaar voor prognose jaar: zet op True om te activeren
SHOW_INGESCHREVEN_JAAR_VOOR = False

# Page title
st.title("📊 Instroomprognose")

prognose_files = get_prognose_files()

if not prognose_files:
    st.warning("⚠️ Geen bestanden geüpload voor Instroomprognose.")
    st.info("💡 Upload de volgende bestanden bij 'Bestanden' → 'Selecteer bestandslocatie':")
    st.markdown("""
    - **Historische jaren:** `inschrijvingen_summary_xxx.csv` (totaal inschrijvingen per jaar)
    - **Prognose:** `predictions_mbo_****_week##.xlsx` (week van 1 oktober, of dichtstbijzijnde week ervoor)
    - **Ingeschreven per week:** `application(s)_enriched_with_context_xxx.csv` (optioneel, upload bij Beschrijving of Instroomprognose)
    """)
    st.stop()

# Separate files by type (prognose + beschrijving voor application_enriched, alleen als SHOW_INGESCHREVEN_JAAR_VOOR)
beschrijving_files = get_beschrijving_files() or []
all_files_for_app = list(prognose_files) + list(beschrijving_files) if SHOW_INGESCHREVEN_JAAR_VOOR else []
inschrijvingen_files = [(f, n, s) for f, n, s in prognose_files if is_inschrijvingen_summary(n)]
prediction_files = [(f, n, s) for f, n, s in prognose_files if is_prediction_mbo(n)]
application_files = [(f, n, s) for f, n, s in all_files_for_app if is_application_enriched(n)] if SHOW_INGESCHREVEN_JAAR_VOOR else []
other_files = [(f, n, s) for f, n, s in prognose_files if not is_inschrijvingen_summary(n) and not is_prediction_mbo(n) and not is_application_enriched(n)]

# Load all data first for filtering
df_inschrijvingen_list = []
for file_obj, file_name, _ in inschrijvingen_files:
    try:
        df = read_data_file(file_obj, file_name)
        if df is not None and not df.empty:
            df_inschrijvingen_list.append(df)
    except Exception:
        pass

df_inschrijvingen = pd.concat(df_inschrijvingen_list, ignore_index=True) if df_inschrijvingen_list else pd.DataFrame()

# Load predictions by year: alleen het bestand met het hoogste weeknummer per jaar
prediction_by_year = {}  # jaar -> list of (file_obj, file_name, week)
for file_obj, file_name, _ in prediction_files:
    parsed = parse_prediction_mbo_filename(file_name)
    if parsed:
        jaar, week = parsed
        if jaar not in prediction_by_year:
            prediction_by_year[jaar] = []
        prediction_by_year[jaar].append((file_obj, file_name, week))

df_predictions_by_year = {}  # jaar -> DataFrame (alleen van bestand met hoogste weeknr)
df_predictions_all_weeks = {}  # jaar -> list of (week, DataFrame) voor per-week grafiek
for jaar, files_list in prediction_by_year.items():
    # Kies bestand met hoogste weeknummer voor totaal-grafiek
    best_file = max(files_list, key=lambda x: x[2])
    file_obj, file_name, week = best_file
    try:
        df = read_excel_file(file_obj, file_name)
        if df is not None and not df.empty:
            df_predictions_by_year[jaar] = df
    except Exception:
        pass
    # Laad alle weekbestanden voor per-week grafiek
    df_predictions_all_weeks[jaar] = []
    for f_obj, f_name, w in files_list:
        try:
            df_w = read_excel_file(f_obj, f_name)
            if df_w is not None and not df_w.empty:
                df_predictions_all_weeks[jaar].append((w, df_w))
        except Exception:
            pass

# Load application_enriched_with_context voor ingeschreven studenten per week
df_application_list = []
for file_obj, file_name, _ in application_files:
    try:
        df = read_data_file(file_obj, file_name) if file_name.lower().endswith('.csv') else read_excel_file(file_obj, file_name)
        if df is not None and not df.empty:
            df_application_list.append(df)
    except Exception:
        pass
df_application = pd.concat(df_application_list, ignore_index=True) if df_application_list else pd.DataFrame()

# Column mappings for filters and aggregatie
INSTELLING_COLS = ['instellingserkenningscode']
# Historische jaren: schooljaar_berekend (inschrijvingen_summary)
SCHOOLJAAR_COLS = ['schooljaar_berekend', 'schooljaar_afgeleid', 'schooljaar', 'collegejaar', 'school_jaar', 'jaar']
LEERWEG_COLS = ['leertraject', 'leertrajectmbo', 'leerweg']
OPLEIDING_COLS = ['opleidingscode', 'opleidingcode', 'code']
# Prognose: Aantal_studenten uit predictions_mbo bestanden
AANTAL_STUDENTEN_COLS = ['aantal_studenten', 'aantal', 'count']
# Prognose: Individual_ratio voor verwacht totaal, Individual_mean voor tweede kolom in grafiek
INDIVIDUAL_RATIO_COLS = ['individual_ratio', 'individual ratio']
INDIVIDUAL_MEAN_COLS = ['individual_mean', 'individual mean']
# Historisch: aantal uit inschrijvingen_summary
AANTAL_HIST_COLS = ['aantal', 'anaal', 'aantal_voorspeld', 'count']
# Application: bsn_hash (unieke studenten), status=ENROLLED, week_of_year, schooljaar_afgeleid
APP_BSN_COLS = ['bsnhash', 'bsn_hash', 'bsn hash']
APP_WEEK_COLS = ['week_of_year', 'weekofyear', 'week']
APP_JAAR_COLS = ['schooljaar_afgeleid', 'schooljaarafgeleid', 'schooljaar']
APP_STATUS_COLS = ['status', 'aanmelding_status']

# Find filter columns in inschrijvingen data
instelling_col = find_column(df_inschrijvingen, INSTELLING_COLS) if not df_inschrijvingen.empty else None
schooljaar_col = find_column(df_inschrijvingen, SCHOOLJAAR_COLS) if not df_inschrijvingen.empty else None
leerweg_col = find_column(df_inschrijvingen, LEERWEG_COLS) if not df_inschrijvingen.empty else None
opleiding_col = find_column(df_inschrijvingen, OPLEIDING_COLS) if not df_inschrijvingen.empty else None
aantal_col_hist = find_column(df_inschrijvingen, AANTAL_HIST_COLS) if not df_inschrijvingen.empty else None

# Also check predictions for filter columns (use first available year)
df_pred_sample = next(iter(df_predictions_by_year.values())) if df_predictions_by_year else pd.DataFrame()
pred_instelling_col = find_column(df_pred_sample, INSTELLING_COLS) if not df_pred_sample.empty else None
pred_schooljaar_col = find_column(df_pred_sample, SCHOOLJAAR_COLS) if not df_pred_sample.empty else None
pred_leerweg_col = find_column(df_pred_sample, LEERWEG_COLS) if not df_pred_sample.empty else None
pred_opleiding_col = find_column(df_pred_sample, OPLEIDING_COLS) if not df_pred_sample.empty else None
aantal_col_pred = find_column(df_pred_sample, AANTAL_STUDENTEN_COLS) if not df_pred_sample.empty else None
individual_ratio_col = find_column(df_pred_sample, INDIVIDUAL_RATIO_COLS) if not df_pred_sample.empty else None
individual_mean_col = find_column(df_pred_sample, INDIVIDUAL_MEAN_COLS) if not df_pred_sample.empty else None

# Application columns: bsn_hash, status=ENROLLED, week_of_year, schooljaar_afgeleid
app_bsn_col = find_column(df_application, APP_BSN_COLS) if not df_application.empty else None
app_week_col = find_column(df_application, APP_WEEK_COLS) if not df_application.empty else None
app_jaar_col = find_column(df_application, APP_JAAR_COLS) if not df_application.empty else None
app_status_col = find_column(df_application, APP_STATUS_COLS) if not df_application.empty else None
app_instelling_col = find_column(df_application, INSTELLING_COLS) if not df_application.empty else None
app_leerweg_col = find_column(df_application, LEERWEG_COLS) if not df_application.empty else None
app_opleiding_col = find_column(df_application, OPLEIDING_COLS) if not df_application.empty else None

# Build filter options from data (inschrijvingen + predictions)
def get_filter_options(df, col):
    if df is None or df.empty or col is None:
        return []
    return sorted(df[col].dropna().astype(str).unique().tolist())

instelling_opts = list(dict.fromkeys(
    get_filter_options(df_inschrijvingen, instelling_col) +
    [v for d in df_predictions_by_year.values() for v in get_filter_options(d, pred_instelling_col)]
))
schooljaar_opts = list(dict.fromkeys(
    get_filter_options(df_inschrijvingen, schooljaar_col) +
    [v for d in df_predictions_by_year.values() for v in get_filter_options(d, pred_schooljaar_col)]
))
leerweg_opts = list(dict.fromkeys(
    get_filter_options(df_inschrijvingen, leerweg_col) +
    [v for d in df_predictions_by_year.values() for v in get_filter_options(d, pred_leerweg_col)]
))
opleiding_opts = list(dict.fromkeys(
    get_filter_options(df_inschrijvingen, opleiding_col) +
    [v for d in df_predictions_by_year.values() for v in get_filter_options(d, pred_opleiding_col)]
))

# Filter UI
st.markdown("### 🔽 Filters")
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    selected_instelling = st.multiselect(
        "Instelling",
        options=instelling_opts,
        default=[],
        key="instroomprognose_filter_instelling"
    )
    selected_schooljaar = st.multiselect(
        "Schooljaar",
        options=schooljaar_opts,
        default=[],
        key="instroomprognose_filter_schooljaar"
    )

with filter_col2:
    selected_leerweg = st.multiselect(
        "Leerweg",
        options=leerweg_opts,
        default=[],
        key="instroomprognose_filter_leerweg"
    )
    selected_opleiding = st.multiselect(
        "Opleiding",
        options=opleiding_opts,
        default=[],
        key="instroomprognose_filter_opleiding"
    )

def apply_filters(df, inst_col, sj_col, lw_col, opl_col):
    if df is None or df.empty:
        return df
    out = df.copy()
    if inst_col and inst_col in out.columns and selected_instelling:
        out = out[out[inst_col].astype(str).isin(selected_instelling)]
    if sj_col and sj_col in out.columns and selected_schooljaar:
        out = out[out[sj_col].astype(str).isin(selected_schooljaar)]
    if lw_col and lw_col in out.columns and selected_leerweg:
        out = out[out[lw_col].astype(str).isin(selected_leerweg)]
    if opl_col and opl_col in out.columns and selected_opleiding:
        out = out[out[opl_col].astype(str).isin(selected_opleiding)]
    return out

# KPI: Studentprognose voor XXXX (bovenaan)
# Toon voor elk prognosejaar: prognose vs voorgaand jaar (op basis van Individual_ratio)
# Gebruik week van 1 oktober, of dichtstbijzijnde week ervoor
for prognose_jaar in sorted(df_predictions_by_year.keys()):
    totaal_prognose = 0
    df_pred = None
    if prognose_jaar in df_predictions_all_weeks and df_predictions_all_weeks[prognose_jaar]:
        available_weeks = [w for w, _ in df_predictions_all_weeks[prognose_jaar]]
        best_week = get_best_week_for_oct1(available_weeks, prognose_jaar)
        if best_week is not None:
            df_pred = next((df for w, df in df_predictions_all_weeks[prognose_jaar] if w == best_week), None)
    if df_pred is None and prognose_jaar in df_predictions_by_year:
        df_pred = df_predictions_by_year[prognose_jaar]  # fallback
    if df_pred is not None:
        df_pred_filt = apply_filters(df_pred, pred_instelling_col, pred_schooljaar_col, pred_leerweg_col, pred_opleiding_col)
        r_col = find_column(df_pred_filt, INDIVIDUAL_RATIO_COLS) if not df_pred_filt.empty else None
        if r_col is None:
            r_col = find_column(df_pred_filt, AANTAL_STUDENTEN_COLS)
        if not df_pred_filt.empty and r_col:
            totaal_prognose = int(df_pred_filt[r_col].sum())
    
    # Voorgaand jaar: som uit inschrijvingen_summary voor jaar-1
    vorig_jaar = prognose_jaar - 1
    totaal_vorig_jaar = 0
    if not df_inschrijvingen.empty and schooljaar_col and aantal_col_hist:
        df_hist_filt = apply_filters(df_inschrijvingen, instelling_col, schooljaar_col, leerweg_col, opleiding_col)
        if not df_hist_filt.empty:
            # Robuuste jaarvergelijking: 2023, 2023.0, "2023", "2022-2023" moeten matchen
            def jaar_equals(val, target):
                if pd.isna(val):
                    return False
                s = str(val).strip()
                # Schooljaar "2022-2023" -> eindjaar 2023
                if '-' in s:
                    try:
                        return int(s.split('-')[-1]) == target
                    except (ValueError, IndexError):
                        pass
                try:
                    return int(float(val)) == target
                except (ValueError, TypeError):
                    return s == str(target)
            mask = df_hist_filt[schooljaar_col].apply(lambda x: jaar_equals(x, vorig_jaar))
            df_vorig = df_hist_filt[mask]
            if not df_vorig.empty:
                totaal_vorig_jaar = int(df_vorig[aantal_col_hist].sum())
    
    # Delta: procent meer/minder t.o.v. voorgaand jaar
    if totaal_vorig_jaar > 0:
        pct = ((totaal_prognose - totaal_vorig_jaar) / totaal_vorig_jaar) * 100
        if pct > 0:
            delta_str = f"{pct:,.1f}% meer t.o.v. {vorig_jaar}"
            delta_color = "normal"  # groen pijltje omhoog
        elif pct < 0:
            delta_str = f"{abs(pct):,.1f}% minder t.o.v. {vorig_jaar}"
            delta_color = "inverse"  # rood pijltje omlaag
        else:
            delta_str = f"0% t.o.v. {vorig_jaar}"
            delta_color = "off"
    else:
        delta_str = None
        delta_color = "off"
    
    st.metric(
        label=f"Studentprognose voor {prognose_jaar}",
        value=f"{totaal_prognose:,}",
        delta=delta_str if delta_str else None,
        delta_color=delta_color
    )

# Aggregate with filters applied
yearly_totals = {}
year_types = {}

# 1. Historical from inschrijvingen_summary: optelsom aantal per schooljaar_berekend
if not df_inschrijvingen.empty:
    if not schooljaar_col or not aantal_col_hist:
        st.warning(f"inschrijvingen_summary: kolommen 'schooljaar_berekend' en 'aantal' niet gevonden. Beschikbaar: {', '.join(df_inschrijvingen.columns)}")
    else:
        df_filtered = apply_filters(df_inschrijvingen, instelling_col, schooljaar_col, leerweg_col, opleiding_col)
        if not df_filtered.empty:
            per_jaar = df_filtered.groupby(schooljaar_col)[aantal_col_hist].sum()
            for jaar in per_jaar.index:
                jaar_val = int(jaar) if pd.notna(jaar) else jaar
                yearly_totals[jaar_val] = yearly_totals.get(jaar_val, 0) + int(per_jaar[jaar])
                year_types[jaar_val] = 'historisch'

# 2. Prognosis from predictions_mbo: optelsom Individual_ratio uit week van 1 oktober (of dichtstbijzijnde week ervoor)
for jaar in df_predictions_by_year.keys():
    df_pred = None
    if jaar in df_predictions_all_weeks and df_predictions_all_weeks[jaar]:
        available_weeks = [w for w, _ in df_predictions_all_weeks[jaar]]
        best_week = get_best_week_for_oct1(available_weeks, jaar)
        if best_week is not None:
            df_pred = next((df for w, df in df_predictions_all_weeks[jaar] if w == best_week), None)
    if df_pred is None:
        df_pred = df_predictions_by_year.get(jaar)  # fallback naar hoogste week
    if df_pred is None:
        continue
    df_filtered = apply_filters(df_pred, pred_instelling_col, pred_schooljaar_col, pred_leerweg_col, pred_opleiding_col)
    if df_filtered.empty:
        continue
    r_col = find_column(df_filtered, INDIVIDUAL_RATIO_COLS)
    if r_col is None:
        r_col = find_column(df_filtered, AANTAL_STUDENTEN_COLS)
    if r_col is None:
        if not df_pred.empty:
            st.warning(f"Prognose {jaar}: kolom 'Individual_ratio' of 'Aantal_studenten' niet gevonden. Beschikbare kolommen: {', '.join(df_pred.columns)}")
        continue
    jaar_total = int(df_filtered[r_col].sum())
    if jaar_total > 0:
        yearly_totals[jaar] = jaar_total
        year_types[jaar] = 'prognose'

# Warn about unprocessed files
if other_files:
    st.info(f"ℹ️ {len(other_files)} bestand(en) overgeslagen (geen inschrijvingen_summary of predictions_mbo bestand): {', '.join(n for _, n, _ in other_files)}")

# Build bar chart data
if not yearly_totals:
    st.warning("⚠️ Geen data gevonden om weer te geven.")
    st.markdown("""
    Zorg dat u de juiste bestanden heeft geüpload:
    - **inschrijvingen_summary_xxx.csv** voor historische aantallen inschrijvingen per jaar
    - **predictions_mbo_****_week##.xlsx** voor de prognose (week van 1 oktober, of dichtstbijzijnde week ervoor)
    - **application(s)_enriched_with_context_xxx.csv** voor ingeschreven per week (upload bij Beschrijving of Instroomprognose)
    """)
    st.stop()

# Sort years and create chart data - x-as per schooljaar (geen weeknummers)
years = sorted(yearly_totals.keys())
totals = [yearly_totals[y] for y in years]
# Labels: alleen schooljaar (geen (prognose) op x-as)
labels = [str(y) for y in years]
colors = ['#636EFA' if year_types.get(y) == 'historisch' else '#EF553B' for y in years]

# Titel: prognosejaar bepalen
prognose_jaren = [y for y in years if year_types.get(y) == 'prognose']
prognose_jaar_tekst = ', '.join(str(y) for y in prognose_jaren) if prognose_jaren else ''
chart_title = f"Ontwikkeling studentaantallen en prognose {prognose_jaar_tekst}: Totaal" if prognose_jaar_tekst else "Ontwikkeling studentaantallen: Totaal"

# Create Plotly bar chart - x-as = schooljaar
fig = go.Figure()
fig.add_trace(go.Bar(
    x=labels,
    y=totals,
    marker_color=colors,
    text=[f"{t:,}" for t in totals],
    textposition='outside',
    textfont=dict(size=12)
))

fig.update_layout(
    title=dict(
        text=chart_title,
        subtitle=dict(text="Blauw = historisch (inschrijvingen_summary) · Rood = prognose (predictions_mbo)", font=dict(style="italic"))
    ),
    xaxis_title='Schooljaar',
    yaxis_title='Aantal studenten',
    xaxis=dict(
        tickangle=-45,
        type='category',
        categoryorder='array',
        categoryarray=labels
    ),
    height=500,
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# Summary metrics
if years:
    max_jaar = years[totals.index(max(totals))]
    st.metric("Jaar met meeste studenten", str(max_jaar))

# Grafiek "Verwacht totaal aantal studenten xxx - per week" voor elk prognosejaar
for prognose_jaar in prognose_jaren:
    if prognose_jaar not in df_predictions_all_weeks or not df_predictions_all_weeks[prognose_jaar]:
        continue
    week_data_list = df_predictions_all_weeks[prognose_jaar]
    # Verzamel (week, totaal) per bestand op basis van Individual_ratio (fallback: Aantal_studenten)
    # en Individual_mean voor de tweede kolom
    weekly_totals_ratio = {}
    weekly_totals_mean = {}
    for week, df_w in week_data_list:
        df_filt = apply_filters(df_w, pred_instelling_col, pred_schooljaar_col, pred_leerweg_col, pred_opleiding_col)
        if df_filt.empty:
            continue
        # Individual_ratio voor verwacht totaal
        r_col = find_column(df_filt, INDIVIDUAL_RATIO_COLS) if not df_filt.empty else None
        if r_col is None:
            r_col = find_column(df_filt, AANTAL_STUDENTEN_COLS)
        if r_col:
            total_ratio = df_filt[r_col].sum()
            weekly_totals_ratio[week] = weekly_totals_ratio.get(week, 0) + total_ratio
        # Individual_mean voor tweede kolom
        m_col = find_column(df_filt, INDIVIDUAL_MEAN_COLS) if not df_filt.empty else None
        if m_col:
            total_mean = df_filt[m_col].sum()
            weekly_totals_mean[week] = weekly_totals_mean.get(week, 0) + total_mean
    # Gebruik ratio-totalen; als geen Individual_ratio, dan weekly_totals_ratio leeg en we skippen
    weekly_totals = weekly_totals_ratio if weekly_totals_ratio else {}
    if not weekly_totals:
        continue
    # Sorteer weken: eerste kolom = week waarin 1 oktober valt
    weeks_sorted = sort_weeks_with_oct1_first(list(weekly_totals.keys()), prognose_jaar)
    values_sorted = [weekly_totals[w] for w in weeks_sorted]
    values_mean_sorted = [weekly_totals_mean.get(w, 0) for w in weeks_sorted] if weekly_totals_mean else []
    # Ingeschreven studenten uit application_enriched (zelfde week, jaar ervoor) - optioneel via SHOW_INGESCHREVEN_JAAR_VOOR
    vorig_jaar = prognose_jaar - 1
    has_ingeschreven = False
    values_ingeschreven_sorted = []
    if SHOW_INGESCHREVEN_JAAR_VOOR:
        weekly_ingeschreven = get_weekly_ingeschreven(
            df_application, vorig_jaar, app_bsn_col, app_week_col, app_jaar_col, app_status_col,
            app_instelling_col, app_leerweg_col, app_opleiding_col
        )
        values_ingeschreven_sorted = [weekly_ingeschreven.get(w, 0) for w in weeks_sorted]
        has_ingeschreven = any(v > 0 for v in values_ingeschreven_sorted)
        # Debug: toon status application data
        with st.expander("🔍 Status application_enriched data", expanded=not has_ingeschreven):
            st.write("**Bestanden:**", len(application_files), "application_enriched bestand(en) gevonden")
            if application_files:
                st.write("Bestandsnamen:", [n for _, n, _ in application_files])
            st.write("**Data geladen:**", len(df_application), "rijen" if not df_application.empty else "Geen data")
            if not df_application.empty:
                st.write("**Kolommen:**", ", ".join(df_application.columns.tolist()[:15]), "..." if len(df_application.columns) > 15 else "")
                st.write("**bsn_hash:**", "✓" if app_bsn_col else "✗", "| **week_of_year:**", "✓" if app_week_col else "✗", "| **schooljaar_afgeleid:**", "✓" if app_jaar_col else "✗", "| **status:**", "✓" if app_status_col else "✗")
                if app_status_col:
                    st.write("**Status waarden:**", df_application[app_status_col].value_counts().head().to_dict())
                if app_jaar_col:
                    st.write("**Schooljaar waarden:**", sorted(df_application[app_jaar_col].dropna().astype(str).unique().tolist())[:10])
                st.write("**Ingeschreven per week (vorig jaar):**", dict(list(weekly_ingeschreven.items())[:10]) if weekly_ingeschreven else "Leeg")
    week_labels = [f"Week {w}" for w in weeks_sorted]
    # Toggle voor tweede kolom (Individual_mean)
    show_individual_mean = st.checkbox(
        "Toon Individual_mean in grafiek",
        value=False,
        key=f"instroomprognose_show_mean_{prognose_jaar}"
    )
    fig_week = go.Figure()
    fig_week.add_trace(go.Bar(
        x=week_labels,
        y=values_sorted,
        name='Individual ratio',
        marker_color='#EF553B'
    ))
    if show_individual_mean and values_mean_sorted:
        fig_week.add_trace(go.Bar(
            x=week_labels,
            y=values_mean_sorted,
            name='Individual mean',
            marker_color='#00CC96'
        ))
    if SHOW_INGESCHREVEN_JAAR_VOOR and has_ingeschreven:
        fig_week.add_trace(go.Bar(
            x=week_labels,
            y=values_ingeschreven_sorted,
            name=f'Ingeschreven {vorig_jaar}',
            marker_color='#636EFA'
        ))
    elif SHOW_INGESCHREVEN_JAAR_VOOR and application_files and not has_ingeschreven:
        st.caption(f"ℹ️ Geen ENROLLED data voor {vorig_jaar}. Vereist: bsn_hash, status, week_of_year, schooljaar_afgeleid.")
    show_legend = show_individual_mean and bool(values_mean_sorted) or has_ingeschreven
    fig_week.update_layout(
        title=f"Verwacht totaal aantal studenten {prognose_jaar} - per week",
        xaxis_title='Week',
        yaxis_title='Aantal studenten',
        xaxis=dict(tickangle=-45),
        height=500,
        barmode='group',
        showlegend=show_legend
    )
    st.plotly_chart(fig_week, use_container_width=True)
    
    # Metrics onder de grafiek (op basis van Individual_ratio)
    # Totaal aantal voorspeld: week 40 of dichtstbijzijnde week ervoor
    totaal_hogste_week = 0
    df_hoogste = None
    if prognose_jaar in df_predictions_all_weeks and df_predictions_all_weeks[prognose_jaar]:
        available_weeks = [w for w, _ in df_predictions_all_weeks[prognose_jaar]]
        best_week = get_best_week_for_oct1(available_weeks, prognose_jaar)  # week 40 of dichtstbij
        if best_week is not None:
            df_hoogste = next((df for w, df in df_predictions_all_weeks[prognose_jaar] if w == best_week), None)
    if df_hoogste is None and prognose_jaar in df_predictions_by_year:
        df_hoogste = df_predictions_by_year[prognose_jaar]  # fallback
    if df_hoogste is not None:
        df_hoogste = apply_filters(df_hoogste, pred_instelling_col, pred_schooljaar_col, pred_leerweg_col, pred_opleiding_col)
        r_col = find_column(df_hoogste, INDIVIDUAL_RATIO_COLS) if not df_hoogste.empty else None
        if r_col is None:
            r_col = find_column(df_hoogste, AANTAL_STUDENTEN_COLS)
        if not df_hoogste.empty and r_col:
            totaal_hogste_week = int(df_hoogste[r_col].sum())
    
    totaal_alle_weken = sum(values_sorted)
    n_weken = len(weeks_sorted)
    gemiddelde_per_week = totaal_alle_weken / n_weken if n_weken > 0 else 0
    
    max_week_idx = values_sorted.index(max(values_sorted)) if values_sorted else 0
    week_meeste = weeks_sorted[max_week_idx] if weeks_sorted else None
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Totaal aantal voorspeld tot nu toe", f"{totaal_hogste_week:,}")
    with m2:
        st.metric("Gemiddeld aantal voorspeld per week", f"{int(gemiddelde_per_week):,}")
    with m3:
        st.metric("Week met de meeste aanmeldingen", f"Week {week_meeste}" if week_meeste is not None else "-")
