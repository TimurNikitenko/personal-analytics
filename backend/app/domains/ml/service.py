"""
Domain Application Service for Machine Learning Datasets.
Transposes, pivots, normalizes, and merges multi-domain personal metrics into a flattened feature matrix.
"""

from typing import List, Optional, Dict, Any
from datetime import date
import pandas as pd
import numpy as np
from sqlalchemy.engine import Engine

class MLDatasetService:
    def __init__(self, engine: Engine):
        self.engine = engine

    def build_flattened_dataset(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        # 1. Daily logs
        query_logs = "SELECT * FROM daily_logs"
        df_logs = pd.read_sql_query(query_logs, con=self.engine)
        if df_logs.empty:
            return []

        df_logs['date'] = pd.to_datetime(df_logs['date'])

        # Calculate sleep hours
        df_logs['sleep_hours'] = np.nan
        for idx, row in df_logs.iterrows():
            if pd.notna(row['sleep_start']) and pd.notna(row['sleep_end']):
                start = pd.to_datetime(row['sleep_start'])
                end = pd.to_datetime(row['sleep_end'])
                if end < start:
                    end = end + pd.Timedelta(days=1)
                df_logs.at[idx, 'sleep_hours'] = (end - start).total_seconds() / 3600.0

        df_logs_base = df_logs[[
            'date', 'mood_score', 'steps', 'workout_minutes',
            'exercise_snacks_count', 'work_hours', 'sleep_hours', 'diary_text'
        ]].copy()

        # 2. Daily supplements pivoted
        query_supp = "SELECT * FROM daily_supplements"
        df_supp = pd.read_sql_query(query_supp, con=self.engine)
        if not df_supp.empty:
            df_supp['date'] = pd.to_datetime(df_supp['date'])
            df_supp['dosage'] = df_supp['dosage'].astype(float)
            df_supp_pivot = df_supp.pivot_table(
                index='date',
                columns='name',
                values='dosage',
                aggfunc='sum'
            ).reset_index()
            df_supp_pivot.columns = ['date'] + [f"supp_{col}" for col in df_supp_pivot.columns[1:]]
        else:
            df_supp_pivot = pd.DataFrame(columns=['date'])

        # 3. Finances pivoted by type
        query_fin = "SELECT * FROM finances"
        df_fin = pd.read_sql_query(query_fin, con=self.engine)
        if not df_fin.empty:
            df_fin['date'] = pd.to_datetime(df_fin['date'])
            df_fin['amount'] = df_fin['amount'].astype(float)
            df_fin_pivot = df_fin.pivot_table(
                index='date',
                columns='transaction_type',
                values='amount',
                aggfunc='sum'
            ).reset_index()
            df_fin_pivot.columns = ['date'] + [f"finance_{col}" for col in df_fin_pivot.columns[1:]]
        else:
            df_fin_pivot = pd.DataFrame(columns=['date'])

        # 4. Learning Logs pivoted by topic
        query_learn = "SELECT * FROM learning_logs"
        df_learn = pd.read_sql_query(query_learn, con=self.engine)
        if not df_learn.empty:
            df_learn['date'] = pd.to_datetime(df_learn['date'])
            df_learn['learning_hours'] = df_learn['learning_hours'].astype(float)
            df_learn['practice_hours'] = df_learn['practice_hours'].astype(float)

            df_learn_theory = df_learn.pivot_table(
                index='date', columns='topic', values='learning_hours', aggfunc='sum'
            ).reset_index()
            df_learn_theory.columns = ['date'] + [f"learn_{col}_theory" for col in df_learn_theory.columns[1:]]

            df_learn_practice = df_learn.pivot_table(
                index='date', columns='topic', values='practice_hours', aggfunc='sum'
            ).reset_index()
            df_learn_practice.columns = ['date'] + [f"learn_{col}_practice" for col in df_learn_practice.columns[1:]]

            df_learn_pivot = pd.merge(df_learn_theory, df_learn_practice, on='date', how='outer')
        else:
            df_learn_pivot = pd.DataFrame(columns=['date'])

        # 5. Global biometrics metrics pivoted
        query_metrics = "SELECT * FROM global_metrics"
        df_metrics = pd.read_sql_query(query_metrics, con=self.engine)
        if not df_metrics.empty:
            df_metrics['date'] = pd.to_datetime(df_metrics['date'])
            df_metrics['num_val'] = pd.to_numeric(df_metrics['metric_value'], errors='coerce')
            df_metrics_pivot = df_metrics.pivot_table(
                index='date',
                columns='metric_name',
                values='num_val',
                aggfunc='last'
            ).reset_index()
            df_metrics_pivot.columns = ['date'] + [f"metric_{col}" for col in df_metrics_pivot.columns[1:]]
        else:
            df_metrics_pivot = pd.DataFrame(columns=['date'])

        # 6. Daily nutrition
        query_nut = "SELECT * FROM daily_nutrition"
        df_nut = pd.read_sql_query(query_nut, con=self.engine)
        if not df_nut.empty:
            df_nut['date'] = pd.to_datetime(df_nut['date'])
            df_nut.columns = ['date'] + [f"nutrition_{col}" for col in df_nut.columns[1:]]
        else:
            df_nut = pd.DataFrame(columns=['date'])

        # 7. Medical tests pivoted
        query_med = "SELECT * FROM medical_tests"
        df_med = pd.read_sql_query(query_med, con=self.engine)
        if not df_med.empty:
            df_med['date'] = pd.to_datetime(df_med['date'])
            df_med['value'] = df_med['value'].astype(float)
            df_med_pivot = df_med.pivot_table(
                index='date',
                columns='test_name',
                values='value',
                aggfunc='last'
            ).reset_index()
            df_med_pivot.columns = ['date'] + [f"med_{col}" for col in df_med_pivot.columns[1:]]
        else:
            df_med_pivot = pd.DataFrame(columns=['date'])

        # Merge datasets
        df_merged = df_logs_base
        for df_to_merge in [df_supp_pivot, df_fin_pivot, df_learn_pivot, df_metrics_pivot, df_nut, df_med_pivot]:
            if not df_to_merge.empty and len(df_to_merge.columns) > 1:
                df_merged = pd.merge(df_merged, df_to_merge, on='date', how='outer')

        if start_date:
            df_merged = df_merged[df_merged['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df_merged = df_merged[df_merged['date'] <= pd.to_datetime(end_date)]

        df_merged = df_merged.sort_values(by='date', ascending=False)
        df_merged['date'] = df_merged['date'].dt.strftime('%Y-%m-%d')
        df_merged = df_merged.replace({np.nan: None})

        return df_merged.to_dict(orient='records')
