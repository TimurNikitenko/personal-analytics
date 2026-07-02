import streamlit as st
import pandas as pd
import numpy as np
import httpx
from datetime import date, datetime, timedelta
from scipy import stats
from scipy.stats import gaussian_kde
import plotly.graph_objects as go
from frontend.utils.api_client import api_client, BACKEND_URL
from frontend.utils.charts import COLORS, apply_sleek_theme

st.set_page_config(page_title="Научные Эксперименты", page_icon="🧪", layout="wide")

# Custom premium CSS styling matching main app style
st.markdown("""
<style>
    .metric-card {
        background: rgba(30, 30, 36, 0.65);
        border: 1px solid rgba(108, 92, 231, 0.15);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(4px);
        transition: transform 0.2s ease-in-out;
        margin-bottom: 15px;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(108, 92, 231, 0.4);
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(45deg, #6C5CE7, #00CEC9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    
    .metric-label {
        font-size: 13px;
        color: #A4A4AB;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .glow-header {
        font-size: 38px;
        font-weight: 900;
        background: linear-gradient(135deg, #00CEC9 0%, #6C5CE7 50%, #A29BFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .scientific-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: bold;
        text-align: center;
    }
    
    .badge-sig {
        background-color: rgba(0, 206, 201, 0.15);
        color: #00CEC9;
        border: 1px solid rgba(0, 206, 201, 0.4);
    }
    
    .badge-nonsig {
        background-color: rgba(250, 177, 160, 0.15);
        color: #FAB1A0;
        border: 1px solid rgba(250, 177, 160, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='glow-header'>🧪 Научные Эксперименты</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #A4A4AB; font-size: 16px; margin-top: -5px;'>Проводите эксперименты над привычками, питанием и биометрией с научной строгостью.</p>", unsafe_allow_html=True)
st.write("---")

# Helper to fetch metric list based on source
def get_metric_choices(source):
    if source == "daily_logs":
        return ["mood_score", "steps", "workout_minutes", "exercise_snacks_count", "work_hours", "sleep_hours"]
    elif source == "global_metrics":
        try:
            return api_client.get_metric_names() or ["Weight", "HRV", "VO2Max"]
        except Exception:
            return ["Weight", "HRV", "VO2Max"]
    elif source == "learning_logs":
        return ["learning_hours", "practice_hours", "total_hours"]
    elif source == "daily_nutrition":
        return ["water_cups", "coffee_cups", "caffeine_mg", "fruits_servings", "vegetables_servings"]
    elif source == "medical_tests":
        return ["Glucose", "Cortisol", "Cholesterol", "Custom"]
    return []

# Helper functions for Plotly charts
def get_kde_points(data, num_points=200):
    if len(data) < 2 or np.std(data) == 0:
        return [], []
    try:
        kde = gaussian_kde(data)
        x = np.linspace(min(data) - np.std(data), max(data) + np.std(data), num_points)
        y = kde(x)
        return x.tolist(), y.tolist()
    except Exception:
        # Fallback if KDE fails due to singular matrix (e.g. constant data)
        return [], []

def get_qq_points(data):
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n < 2:
        return [], []
    quantiles = np.linspace(0.01, 0.99, n)
    theoretical = stats.norm.ppf(quantiles, loc=np.mean(sorted_data), scale=np.std(sorted_data))
    return theoretical.tolist(), sorted_data

# Session state initialization for analysis select
if "active_analysis_id" not in st.session_state:
    st.session_state.active_analysis_id = None
if "just_created_exp" not in st.session_state:
    st.session_state.just_created_exp = None
if "run_analysis_on_load" not in st.session_state:
    st.session_state.run_analysis_on_load = False

# Check if an experiment was just created and show notification banner
if st.session_state.get("just_created_exp"):
    try:
        temp_exps = api_client.get_experiments()
        exp_obj = next((e for e in temp_exps if e["id"] == st.session_state.just_created_exp), None)
    except Exception:
        exp_obj = None
        
    if exp_obj:
        st.markdown(f"""
        <div style="background-color: rgba(108, 92, 231, 0.15); border: 1px solid #6C5CE7; border-radius: 12px; padding: 15px; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #E1E1E6; display: flex; align-items: center; gap: 8px;">🚀 Эксперимент «{exp_obj['title']}» успешно запущен в работу!</h4>
            <p style="margin: 8px 0 12px 0; color: #A4A4AB; font-size: 14px; line-height: 1.5;">
                <b>Гипотеза:</b> {exp_obj['hypothesis']}<br>
                <b>Дизайн:</b> {'До/После (Pre-Post) по историческим логам' if exp_obj['experiment_type'] == 'pre_post' else 'Случайные A/B дни (Randomized)'}<br>
                Вы можете запустить быстрый научный анализ (система соберет имеющиеся исторические логи) или перейти к заполнению журнала дней.
            </p>
        </div>
        """, unsafe_allow_html=True)
        col_banner1, col_banner2, col_banner3 = st.columns([2, 2, 1])
        with col_banner1:
            if st.button("📊 Быстрый научный анализ", key="btn_banner_quick_anal", use_container_width=True):
                st.session_state.active_analysis_id = exp_obj["id"]
                st.session_state.run_analysis_on_load = True
                st.session_state.just_created_exp = None
                st.toast("Анализируем эксперимент...")
                st.rerun()
        with col_banner2:
            if exp_obj["experiment_type"] == "randomized_days":
                if st.button("📝 Перейти в журнал дней", key="btn_banner_quick_log", use_container_width=True):
                    st.session_state.just_created_exp = None
                    st.toast("Перейдите на вкладку 'Журналирование дней'")
                    st.rerun()
            else:
                st.write("")
        with col_banner3:
            if st.button("✕ Скрыть", key="btn_banner_quick_close", use_container_width=True):
                st.session_state.just_created_exp = None
                st.rerun()

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Текущие эксперименты", 
    "🧪 Запланировать эксперимент", 
    "📝 Журналирование дней", 
    "📊 Научный анализ"
])

# Fetch all experiments
try:
    all_experiments = api_client.get_experiments()
except Exception as e:
    all_experiments = []
    st.error("Не удалось подключиться к серверу API.")

# ==================== TAB 1: DASHBOARD ====================
with tab1:
    st.subheader("Список экспериментов")
    
    if not all_experiments:
        st.info("Вы пока не запланировали ни одного эксперимента. Перейдите во вкладку 'Запланировать эксперимент'!")
    else:
        # Filter into Active vs Completed/Cancelled
        active_exps = [e for e in all_experiments if e["status"] == "Active"]
        past_exps = [e for e in all_experiments if e["status"] in ["Completed", "Cancelled"]]
        draft_exps = [e for e in all_experiments if e["status"] == "Draft"]

        if active_exps:
            st.markdown("### 🚀 Активные эксперименты")
            for exp in active_exps:
                with st.expander(f"🔬 {exp['title']} (Старт: {exp['start_date']})", expanded=True):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.markdown(f"**Гипотеза**: {exp['hypothesis']}")
                        st.markdown(f"**Интервенция**: {exp['intervention_description']}")
                        st.markdown(f"**Дизайн**: `{'До/После (Pre-Post)' if exp['experiment_type'] == 'pre_post' else 'Случайные A/B дни (Randomized)'}`")
                    with col2:
                        st.markdown(f"**Целевая метрика**: `{exp['metric_name']}` (Источник: `{exp['metric_source']}`)")
                        st.markdown(f"**Параметры**: $\\alpha = {exp['alpha']}$, Мощность = ${exp['power']}$")
                        st.markdown(f"**Требуемый объем**: по `{exp['required_sample_size'] or 'N/A'}` дней в каждой группе")
                    with col3:
                        # Actions
                        if st.button("📊 Анализировать", key=f"btn_anal_{exp['id']}", use_container_width=True):
                            st.session_state.active_analysis_id = exp["id"]
                            st.session_state.run_analysis_on_load = True
                            st.toast("Перенаправляем во вкладку анализа...")
                            st.rerun()
                            
                        subcol1, subcol2 = st.columns(2)
                        with subcol1:
                            if st.button("✅ Готово", key=f"btn_comp_{exp['id']}", help="Завершить эксперимент"):
                                exp["status"] = "Completed"
                                exp["end_date"] = date.today().isoformat()
                                api_client.update_experiment(exp["id"], exp)
                                st.success("Эксперимент успешно завершен!")
                                st.rerun()
                        with subcol2:
                            if st.button("❌ Отмена", key=f"btn_canc_{exp['id']}", help="Отменить эксперимент"):
                                exp["status"] = "Cancelled"
                                exp["end_date"] = date.today().isoformat()
                                api_client.update_experiment(exp["id"], exp)
                                st.warning("Эксперимент отменен.")
                                st.rerun()
                                
                        if st.button("🗑️ Удалить", key=f"btn_del_{exp['id']}", type="secondary", use_container_width=True):
                            api_client.delete_experiment(exp["id"])
                            st.success("Эксперимент удален.")
                            st.rerun()
                    st.write("---")

        if draft_exps:
            st.markdown("### 📝 Черновики")
            for exp in draft_exps:
                with st.expander(f"📝 {exp['title']} (Черновик)"):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"**Гипотеза**: {exp['hypothesis']}")
                        st.markdown(f"**Интервенция**: {exp['intervention_description']}")
                    with col2:
                        st.markdown(f"**Метрика**: `{exp['metric_name']}` (от `{exp['metric_source']}`)")
                        st.markdown(f"**MDE**: `{exp['mde'] or 'Не задан'}`")
                    with col3:
                        if st.button("🚀 Запустить", key=f"btn_start_{exp['id']}", use_container_width=True):
                            exp["status"] = "Active"
                            exp["start_date"] = date.today().isoformat()
                            api_client.update_experiment(exp["id"], exp)
                            st.success("Эксперимент запущен!")
                            st.rerun()
                        if st.button("🗑️ Удалить", key=f"btn_del_draft_{exp['id']}", type="secondary", use_container_width=True):
                            api_client.delete_experiment(exp["id"])
                            st.success("Черновик удален.")
                            st.rerun()

        if past_exps:
            st.markdown("### 📜 Завершенные / Отмененные эксперименты")
            for exp in past_exps:
                status_emoji = "✅" if exp["status"] == "Completed" else "❌"
                with st.expander(f"{status_emoji} {exp['title']} (Конец: {exp['end_date']})"):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"**Гипотеза**: {exp['hypothesis']}")
                        st.markdown(f"**Дизайн**: `{exp['experiment_type']}`")
                        if exp.get("results_summary"):
                            res = exp["results_summary"]
                            sig = res.get("stat_significant", False)
                            badge_style = "badge-sig" if sig else "badge-nonsig"
                            badge_text = "ЗНАЧИМО" if sig else "НЕЗНАЧИМО"
                            st.markdown(f"**Результат**: <span class='scientific-badge {badge_style}'>{badge_text}</span> (p-value: `{res.get('p_value', 1.0):.4f}`)", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"**Метрика**: `{exp['metric_name']}`")
                        if exp.get("results_summary"):
                            res = exp["results_summary"]
                            st.markdown(f"**Эффект (Cohen's d)**: `{res.get('cohens_d', 0.0):.2f}`")
                            st.markdown(f"**Изменение**: `{res.get('rel_diff', 0.0):+.1f}%` ({res.get('abs_diff', 0.0):+.2f} ед.)")
                    with col3:
                        if st.button("📊 Посмотреть отчет", key=f"btn_view_{exp['id']}", use_container_width=True):
                            st.session_state.active_analysis_id = exp["id"]
                            st.session_state.run_analysis_on_load = True
                            st.toast("Перенаправляем во вкладку анализа...")
                            st.rerun()
                        if st.button("🗑️ Удалить запись", key=f"btn_del_past_{exp['id']}", type="secondary", use_container_width=True):
                            api_client.delete_experiment(exp["id"])
                            st.success("Запись удалена.")
                            st.rerun()

# ==================== TAB 2: PLANNING WIZARD ====================
with tab2:
    st.subheader("🔬 Планирование нового эксперимента")
    st.write("Сделайте расчеты размера выборки (Power Analysis) на основе ваших исторических данных перед началом интервенции.")

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        w_title = st.text_input("Название эксперимента", placeholder="например: Матча вместо Кофе для сна")
        w_hyp = st.text_area("Научная гипотеза", placeholder="например: Замена утреннего кофе на матчу снизит пульс в покое и увеличит среднюю оценку настроения на 1 балл.")
        w_int = st.text_area("Интервенция (Что конкретно меняется?)", placeholder="например: Не пить кофе совсем. Пить 1 чашку (2г) чая матча до 12:00 дня.")
        
    with col_w2:
        st.markdown("#### 🎯 Целевой показатель (Метрика)")
        w_source = st.selectbox("Источник метрики", ["daily_logs", "global_metrics", "learning_logs", "daily_nutrition", "medical_tests"], key="w_source_select")
        
        choices = get_metric_choices(w_source)
        if w_source == "global_metrics":
            w_metric = st.selectbox("Название метрики", choices, key="w_metric_select")
        elif w_source == "medical_tests":
            w_metric_custom = st.text_input("Название медицинского анализа (например: Glucose)", "Cortisol")
            w_metric = w_metric_custom
        else:
            w_metric = st.selectbox("Название метрики", choices, key="w_metric_select")

        # Baseline button
        baseline_mean, baseline_std = 0.0, 0.0
        baseline_n = 0
        if st.button("📥 Загрузить исторический базовый уровень (Baseline)"):
            try:
                base_data = api_client.get_metric_baseline_stats(w_source, w_metric)
                baseline_mean = base_data.get("mean", 0.0)
                baseline_std = base_data.get("std", 0.0)
                baseline_n = base_data.get("n", 0)
                
                st.session_state.baseline_mean = baseline_mean
                st.session_state.baseline_std = baseline_std
                st.session_state.baseline_n = baseline_n
                st.success(f"Найдено {baseline_n} исторических записей! Среднее: {baseline_mean:.2f}, Отклонение (std): {baseline_std:.2f}")
            except Exception as e:
                st.error(f"Не удалось загрузить базовые данные: {e}")

        # Display stored values from session state
        b_mean = st.session_state.get("baseline_mean", 0.0)
        b_std = st.session_state.get("baseline_std", 0.0)
        b_n = st.session_state.get("baseline_n", 0)
        
        if b_n > 0:
            st.caption(f"Текущий базовый уровень: Среднее = **{b_mean:.2f}**, Std = **{b_std:.2f}** (выборка: {b_n} дней)")
        else:
            st.warning("Базовый уровень не загружен. Введите параметры вручную ниже, если требуется.")
            b_std = st.number_input("Оценочное стандартное отклонение (std)", min_value=0.01, value=1.0, step=0.1)

    st.write("---")
    st.markdown("#### ⚙️ Настройки статкритерия и длительности")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        w_type = st.selectbox("Дизайн эксперимента", [("pre_post", "До/После (Pre-Post)"), ("randomized_days", "Случайные A/B дни (Randomized)")])
        w_start = st.date_input("Дата начала эксперимента", date.today())
        if w_type[0] == "pre_post":
            st.info("💡 **Ретроспективный анализ**: Если вы хотите провести анализ уже накопленных исторических данных (например, сравнить период до начала приема БАДа с периодом после), выберите дату начала интервенции в прошлом. Все дни до неё станут группой «Контроль», а дни после нее — «Интервенция».")
    with col_p2:
        w_alpha = st.slider("Уровень значимости (Alpha - ложноположительный порог)", 0.01, 0.20, 0.05, step=0.01)
        w_power = st.slider("Статистическая мощность (1 - Beta)", 0.50, 0.99, 0.80, step=0.05)
    with col_p3:
        # Default MDE is 0.5 * std if std is loaded
        default_mde = float(round(0.5 * b_std, 2)) if b_std > 0 else 0.5
        w_mde = st.number_input("Минимальный обнаруживаемый эффект (MDE)", min_value=0.001, value=default_mde, step=0.1, help="Какое минимальное изменение метрики вы хотите надежно зафиксировать?")

    # Calculate power analysis
    req_n = 0
    if b_std > 0 and w_mde > 0:
        req_n = api_client.get_metric_baseline_stats(w_source, w_metric).get("std", b_std) # use latest or form
        # We can run the calculation locally in frontend too
        z_alpha = stats.norm.ppf(1 - w_alpha / 2)
        z_beta = stats.norm.ppf(w_power)
        req_n = int(np.ceil(2 * (b_std ** 2) * ((z_alpha + z_beta) ** 2) / (w_mde ** 2)))
        
        st.markdown("##### 📊 Расчет длительности эксперимента:")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{req_n} дней</div>
                <div class="metric-label">На одну группу</div>
            </div>
            """, unsafe_allow_html=True)
        with col_c2:
            total_days = req_n * 2
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_days} дней</div>
                <div class="metric-label">Общая длительность</div>
            </div>
            """, unsafe_allow_html=True)
        with col_c3:
            est_end = w_start + timedelta(days=total_days)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{est_end.strftime('%d.%m.%Y')}</div>
                <div class="metric-label">Приблизительная дата окончания</div>
            </div>
            """, unsafe_allow_html=True)

    if st.button("🚀 Создать и запустить эксперимент", use_container_width=True):
        if not w_title.strip() or not w_hyp.strip():
            st.error("Пожалуйста, заполните название эксперимента и формулировку гипотезы.")
        else:
            payload = {
                "title": w_title.strip(),
                "hypothesis": w_hyp.strip(),
                "metric_source": w_source,
                "metric_name": w_metric,
                "intervention_description": w_int.strip(),
                "experiment_type": w_type[0],
                "start_date": w_start.isoformat(),
                "alpha": w_alpha,
                "power": w_power,
                "mde": w_mde,
                "required_sample_size": req_n if req_n > 0 else None,
                "status": "Active"
            }
            try:
                new_exp = api_client.create_experiment(payload)
                st.session_state.just_created_exp = new_exp["id"]
                st.toast("🎉 Эксперимент успешно создан и запущен!")
                st.rerun()
            except Exception as e:
                st.error(f"Не удалось создать эксперимент: {e}")

# ==================== TAB 3: LOGGING DAYS ====================
with tab3:
    st.subheader("📝 Ежедневное журналирование интервенций")
    st.write("Для рандомизированных экспериментов (A/B) отмечайте, какой протокол вы соблюдали в конкретный день.")

    # Filter active randomized experiments
    active_rand_exps = [e for e in all_experiments if e["status"] == "Active" and e["experiment_type"] == "randomized_days"]
    
    if not active_rand_exps:
        st.info("Нет активных экспериментов со случайными днями (Randomized A/B). Создайте эксперимент с этим типом дизайна во вкладке 2.")
    else:
        # Select active exp
        exp_options = {e["id"]: f"🔬 {e['title']}" for e in active_rand_exps}
        selected_exp_id = st.selectbox("Выберите эксперимент", list(exp_options.keys()), format_func=lambda x: exp_options[x], key="logging_exp_select")
        
        exp_obj = next(e for e in active_rand_exps if e["id"] == selected_exp_id)
        
        # Logging form
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            log_date = st.date_input("Дата дня", date.today(), key="log_day_date")
            log_group = st.selectbox("Группа дня (Протокол)", ["Control", "Treatment"], format_func=lambda x: "Контроль (Обычный день)" if x == "Control" else "Эксперимент (Интервенция)")
            log_notes = st.text_input("Заметки о самочувствии / Пропуски", placeholder="например: Забыл выпить вовремя, но протокол соблюдал", key="log_day_notes")
            
            if st.button("➕ Сохранить запись дня", use_container_width=True):
                day_payload = {
                    "date": log_date.isoformat(),
                    "group": log_group,
                    "notes": log_notes.strip() if log_notes.strip() else None
                }
                try:
                    api_client.upsert_experiment_day(selected_exp_id, day_payload)
                    st.success(f"Запись дня {log_date} успешно сохранена!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Не удалось сохранить запись: {e}")
                    
        with col_l2:
            # Show progress bar
            try:
                logged_days = api_client.get_experiment_days(selected_exp_id)
            except Exception:
                logged_days = []
                
            n_control = sum(1 for d in logged_days if d["group"] == "Control")
            n_treatment = sum(1 for d in logged_days if d["group"] == "Treatment")
            target_n = exp_obj["required_sample_size"] or 15
            
            st.markdown("#### 📈 Прогресс сбора данных")
            
            # Control progress
            control_pct = min(1.0, n_control / target_n) if target_n > 0 else 0.0
            st.write(f"Группа контроля: **{n_control}** / **{target_n}** дней")
            st.progress(control_pct)
            
            # Treatment progress
            treatment_pct = min(1.0, n_treatment / target_n) if target_n > 0 else 0.0
            st.write(f"Группа интервенции: **{n_treatment}** / **{target_n}** дней")
            st.progress(treatment_pct)

        # Show table of logged days
        st.write("---")
        st.write("#### 📜 Журнал уже внесенных дней:")
        if not logged_days:
            st.caption("Дни пока не вносились.")
        else:
            df_days = pd.DataFrame(logged_days)
            for idx, row in df_days.iterrows():
                col_d1, col_d2, col_d3, col_d4 = st.columns([2, 2, 4, 1])
                with col_d1:
                    st.write(f"📅 **{row['date']}**")
                with col_d2:
                    grp_label = "🟢 Контроль" if row['group'] == "Control" else "⚡ Интервенция"
                    st.write(grp_label)
                with col_d3:
                    st.write(row['notes'] or "-")
                with col_d4:
                    if st.button("🗑️", key=f"del_day_{row['date']}", help="Удалить запись дня"):
                        try:
                            api_client.delete_experiment_day(selected_exp_id, row['date'])
                            st.warning("Запись дня удалена.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Ошибка удаления: {e}")

# ==================== TAB 4: SCIENTIFIC ANALYSIS ====================
with tab4:
    st.subheader("📊 Научный статистический анализ результатов")
    
    if not all_experiments:
        st.info("Эксперименты отсутствуют.")
    else:
        # Select box for analysis
        exp_dict = {e["id"]: f"🔬 {e['title']} ({'Активен' if e['status'] == 'Active' else 'Завершен/Отменен'})" for e in all_experiments}
        
        # Check if redirected from dashboard
        default_index = 0
        active_id = st.session_state.get("active_analysis_id")
        if active_id in exp_dict:
            default_index = list(exp_dict.keys()).index(active_id)
            
        selected_anal_id = st.selectbox("Выберите эксперимент для проведения анализа", list(exp_dict.keys()), index=default_index, format_func=lambda x: exp_dict[x], key="analysis_exp_select")
        
        # Determine if we should trigger analysis on load
        trigger_analysis = False
        if st.session_state.get("run_analysis_on_load") and selected_anal_id == active_id:
            trigger_analysis = True
            st.session_state.run_analysis_on_load = False
            st.session_state.active_analysis_id = None
            
        selected_exp = next(e for e in all_experiments if e["id"] == selected_anal_id)
        
        # User trigger button or auto-run
        btn_pressed = st.button("📊 Провести анализ и построить графики", use_container_width=True)
        if btn_pressed:
            trigger_analysis = True
            
        report = None
        if trigger_analysis:
            with st.spinner("Загрузка данных и проведение бутстрап-моделирования (2000 симуляций)..."):
                try:
                    report = api_client.analyze_experiment(selected_anal_id)
                except Exception as e:
                    st.error(f"Не удалось провести анализ. Возможно, нет данных в базе: {e}")
                    report = None
                    
            if report:
                if "error" in report:
                    st.error(f"⚠️ {report['error']}")
                else:
                    # Descriptive stats cards
                    c_stats = report["control_stats"]
                    t_stats = report["treatment_stats"]
                    
                    st.markdown("### 📋 Базовые показатели групп")
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    with col_m1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{c_stats['mean']:.2f}</div>
                            <div class="metric-label">Контроль (Ср, n={c_stats['n']})</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_m2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{t_stats['mean']:.2f}</div>
                            <div class="metric-label">Интервенция (Ср, n={t_stats['n']})</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_m3:
                        val_diff = f"{report['rel_diff']:+.1f}%" if report['rel_diff'] != 0 else "0.0%"
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{val_diff}</div>
                            <div class="metric-label">Относительное изменение</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_m4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{report['cohens_d']:.2f}</div>
                            <div class="metric-label">Размер эффекта (Cohen's d)</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    # Statistical Power Summary block
                    st.write("---")
                    st.markdown("#### ⚡ Статистическая мощность (Sensitivity)")
                    
                    achieved_pwr = report.get("achieved_power", 0.0)
                    planned_pwr = selected_exp.get("power", 0.8)
                    req_size = selected_exp.get("required_sample_size") or 0
                    
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        st.markdown(f"**Запланированная мощность**: `{planned_pwr * 100:.0f}%` (при MDE = `{selected_exp['mde']}`)")
                        st.markdown(f"**Текущая мощность (набранная)**: `{achieved_pwr * 100:.1f}%` ({'достаточная' if achieved_pwr >= planned_pwr else 'заниженная'})")
                    with col_p2:
                        st.markdown(f"**Собрано дней**: Контроль `n = {c_stats['n']}`, Интервенция `n = {t_stats['n']}`")
                        st.markdown(f"**Целевой объем**: по `{req_size}` дней на группу")
                    
                    if achieved_pwr < planned_pwr:
                        st.warning(f"""
                        ⚠️ **Внимание: Низкая статистическая мощность ({achieved_pwr * 100:.1f}%)!**
                        Объем собранных данных пока ниже расчетного целевого уровня ({req_size} дней). 
                        При низкой мощности выше вероятность получить ложноотрицательный результат (т.е. не заметить реального эффекта от интервенции). 
                        Рекомендуется продолжить сбор данных для получения достоверного вывода.
                        """)
                    else:
                        st.success(f"""
                        ✅ **Статистическая мощность набрана ({achieved_pwr * 100:.1f}%)!**
                        Объем выборки достаточен для обнаружения эффекта MDE = {selected_exp['mde']}. Полученные результаты статистически надежны.
                        """)
                        
                    # Statistical summary alert
                    sig = report["stat_significant"]
                    badge_style = "badge-sig" if sig else "badge-nonsig"
                    badge_text = "СТАТИСТИЧЕСКИ ЗНАЧИМ" if sig else "СТАТИСТИЧЕСКИ НЕ ЗНАЧИМ"
                    
                    st.write("---")
                    st.markdown(f"#### 🎓 Научный вывод:")
                    
                    effect_size_val = abs(report['cohens_d'])
                    if effect_size_val < 0.2:
                        eff_desc = "отсутствует или пренебрежимо мал"
                    elif effect_size_val < 0.5:
                        eff_desc = "слабый"
                    elif effect_size_val < 0.8:
                        eff_desc = "средней величины"
                    else:
                        eff_desc = "сильный (выраженный)"
                        
                    if sig:
                        st.info(f"""
                        Результат эксперимента **{badge_text}** (p-value = **{report['p_value']:.4f}** при $\\alpha={selected_exp['alpha']}$). 
                        Рекомендуемый критерий: **{report['recommended_test']}**.
                        
                        Мы имеем достаточные статистические основания утверждать, что интервенция изменила целевой показатель `{selected_exp['metric_name']}`. 
                        Наблюдаемый эффект: **{eff_desc}** (Cohen's $d = {report['cohens_d']:.2f}$).
                        Среднее различие составляет **{report['abs_diff']:+.2f}** ед. с 95% доверительным интервалом от **{report['confidence_interval']['lower']:.2f}** до **{report['confidence_interval']['upper']:.2f}**.
                        """)
                    else:
                        st.warning(f"""
                        Результат эксперимента **{badge_text}** (p-value = **{report['p_value']:.4f}** при $\\alpha={selected_exp['alpha']}$). 
                        Рекомендуемый критерий: **{report['recommended_test']}**.
                        
                        У нас **недостаточно данных** или оснований утверждать, что наблюдаемые различия вызваны именно интервенцией (они могут быть следствием случайных колебаний). 
                        Доверительный интервал разности включает ноль: от **{report['confidence_interval']['lower']:.2f}** до **{report['confidence_interval']['upper']:.2f}**.
                        Рекомендуется либо увеличить объем выборки, либо признать интервенцию неэффективной.
                        """)
                        
                    # Statistical assumptions details expander
                    with st.expander("🔬 Подробные результаты проверки стат-критериев и допущений"):
                        col_a1, col_a2 = st.columns(2)
                        with col_a1:
                            st.write("**Тест на нормальность (Shapiro-Wilk):**")
                            nc = report["normality_check"]["control"]
                            nt = report["normality_check"]["treatment"]
                            st.write(f"- Группа контроля: p-val = `{nc.get('p_value', 0.0):.4f}` ({'нормально' if nc.get('is_normal') else 'распределение не нормальное'})")
                            st.write(f"- Группа интервенции: p-val = `{nt.get('p_value', 0.0):.4f}` ({'нормально' if nt.get('is_normal') else 'распределение не нормальное'})")
                            st.caption("Если p-value > 0.05, мы не отвергаем гипотезу о нормальности.")
                        with col_a2:
                            st.write("**Равенство дисперсий (Levene's test):**")
                            v = report["homogeneity_check"]
                            st.write(f"- Дисперсии групп: p-val = `{v.get('p_value', 0.0):.4f}` ({'однородны' if v.get('equal_variance') else 'различаются'})")
                            st.caption("Если p-value > 0.05, дисперсии считаются одинаковыми (гомоскедастичность).")
                            
                        st.write("**Сравнение p-value всех критериев:**")
                        st.write(report["all_tests_p_values"])
                        
                    # Plots Section
                    st.write("---")
                    st.markdown("### 📈 Визуализации")
                    
                    timeline = report.get("timeline", [])
                    if timeline:
                        # Timeline plot
                        df_time = pd.DataFrame(timeline)
                        df_time["date"] = pd.to_datetime(df_time["date"])
                        
                        fig_time = go.Figure()
                        
                        # Control points
                        ctrl = df_time[df_time["group"] == "Control"]
                        fig_time.add_trace(go.Scatter(
                            x=ctrl["date"], y=ctrl["value"],
                            mode="markers+lines",
                            name="Контроль (Control)",
                            line=dict(color="#FAB1A0", width=1.5),
                            marker=dict(size=6)
                        ))
                        # Mean Control line
                        fig_time.add_shape(
                            type="line", line=dict(color="#FAB1A0", dash="dash"),
                            x0=df_time["date"].min(), x1=df_time["date"].max(),
                            y0=c_stats["mean"], y1=c_stats["mean"]
                        )
                        
                        # Treatment points
                        treat = df_time[df_time["group"] == "Treatment"]
                        fig_time.add_trace(go.Scatter(
                            x=treat["date"], y=treat["value"],
                            mode="markers+lines",
                            name="Интервенция (Treatment)",
                            line=dict(color="#00CEC9", width=1.5),
                            marker=dict(size=6)
                        ))
                        # Mean Treatment line
                        fig_time.add_shape(
                            type="line", line=dict(color="#00CEC9", dash="dash"),
                            x0=df_time["date"].min(), x1=df_time["date"].max(),
                            y0=t_stats["mean"], y1=t_stats["mean"]
                        )
                        
                        fig_time.update_layout(
                            title="Хронологический ход эксперимента",
                            xaxis_title="Дата",
                            yaxis_title=selected_exp["metric_name"],
                            template="plotly_dark",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig_time, use_container_width=True)
                        
                    # Distribution KDE & Bootstrap Plots Side by Side
                    col_plt1, col_plt2 = st.columns(2)
                    
                    with col_plt1:
                        # KDE Plot
                        timeline_df = pd.DataFrame(timeline)
                        c_vals = timeline_df[timeline_df["group"] == "Control"]["value"].tolist()
                        t_vals = timeline_df[timeline_df["group"] == "Treatment"]["value"].tolist()
                        
                        fig_kde = go.Figure()
                        
                        xc, yc = get_kde_points(c_vals)
                        if xc:
                            fig_kde.add_trace(go.Scatter(
                                x=xc, y=yc, mode="lines", fill="tozeroy",
                                name="Контроль (KDE)",
                                line=dict(color="#FAB1A0", width=2),
                                fillcolor="rgba(250, 177, 160, 0.15)"
                            ))
                        fig_kde.add_trace(go.Box(
                            x=c_vals, name="Контроль (Box)",
                            marker=dict(color="#FAB1A0"),
                            boxpoints="all", jitter=0.3, pointpos=-1.8
                        ))
                        
                        xt, yt = get_kde_points(t_vals)
                        if xt:
                            fig_kde.add_trace(go.Scatter(
                                x=xt, y=yt, mode="lines", fill="tozeroy",
                                name="Интервенция (KDE)",
                                line=dict(color="#00CEC9", width=2),
                                fillcolor="rgba(0, 206, 201, 0.15)"
                            ))
                        fig_kde.add_trace(go.Box(
                            x=t_vals, name="Интервенция (Box)",
                            marker=dict(color="#00CEC9"),
                            boxpoints="all", jitter=0.3, pointpos=-1.8
                        ))
                        
                        fig_kde.update_layout(
                            title="Плотность распределения и разброс данных",
                            xaxis_title=selected_exp["metric_name"],
                            yaxis_title="Плотность",
                            template="plotly_dark",
                            boxmode="group"
                        )
                        st.plotly_chart(fig_kde, use_container_width=True)
                        
                    with col_plt2:
                        # Bootstrap Histogram
                        boot_data = report.get("bootstrap", {})
                        boot_diffs = boot_data.get("bootstrap_means_diff", [])
                        
                        if boot_diffs:
                            ci_lower = boot_data["ci_lower"]
                            ci_upper = boot_data["ci_upper"]
                            
                            fig_boot = go.Figure()
                            fig_boot.add_trace(go.Histogram(
                                x=boot_diffs,
                                nbinsx=50,
                                name="Разница средних",
                                marker_color="#6C5CE7",
                                opacity=0.75
                            ))
                            
                            # Add vertical lines for CI
                            fig_boot.add_vline(x=ci_lower, line_dash="dash", line_color="#E1E1E6", annotation_text="2.5%")
                            fig_boot.add_vline(x=ci_upper, line_dash="dash", line_color="#E1E1E6", annotation_text="97.5%")
                            
                            # Add zero vertical line
                            fig_boot.add_vline(x=0.0, line_color="#FAB1A0", line_width=2, annotation_text="Ноль (Эффекта нет)")
                            
                            fig_boot.update_layout(
                                title="Бутстрап-распределение разности средних (2000 ресемплов)",
                                xaxis_title="Разница средних (Интервенция - Контроль)",
                                yaxis_title="Частота",
                                template="plotly_dark"
                            )
                            st.plotly_chart(fig_boot, use_container_width=True)
                        else:
                            st.info("Бутстрап-данные отсутствуют или не рассчитывались.")
