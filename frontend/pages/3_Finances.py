import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from decimal import Decimal
from frontend.utils.api_client import api_client
from frontend.utils.charts import COLORS, create_pie_chart, create_timeline_chart

st.set_page_config(page_title="Finances", page_icon="💸", layout="wide")

# Custom header
st.markdown("<h1 style='background: linear-gradient(135deg, #FDCB6E, #E17055); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:900;'>💸 Finance Tracker & Analytics</h1>", unsafe_allow_html=True)
st.write("Manage manual expenses/savings, upload bank statement CSV files, and track your cash flow.")

# Tabs for entry vs analysis
tab1, tab2, tab3 = st.tabs(["📊 Analytics & Dashboards", "➕ Add Transaction", "📁 CSV Import Bank Statements"])

# Date filters at top level
st.sidebar.markdown("### 📅 Date Filters")
start_date = st.sidebar.date_input("Start Date", date.today() - timedelta(days=90))
end_date = st.sidebar.date_input("End Date", date.today())

# Fetch transaction list
try:
    transactions = api_client.get_finances(start_date=start_date, end_date=end_date)
except Exception:
    st.error("Could not load finances from backend database.")
    transactions = []

df_fin = pd.DataFrame(transactions)
if not df_fin.empty:
    df_fin['date'] = pd.to_datetime(df_fin['date'])
    df_fin['amount'] = df_fin['amount'].astype(float)

# ==================== TAB 1: ANALYTICS & DASHBOARDS ====================
with tab1:
    if df_fin.empty:
        st.info("No financial transactions logged in this period. Add transactions or import a CSV to begin!")
    else:
        # Cash Flow Calculations
        income = df_fin[df_fin["transaction_type"] == "Income"]["amount"].sum()
        expenses = df_fin[df_fin["transaction_type"] == "Expense"]["amount"].sum()
        savings = df_fin[df_fin["transaction_type"] == "Saving"]["amount"].sum()

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Total Income", f"${income:,.2f}")
        with col_m2:
            st.metric("Total Expenses", f"${expenses:,.2f}")
        with col_m3:
            st.metric("Logged Savings", f"${savings:,.2f}")
        with col_m4:
            st.metric("Implied Net Cash Flow", f"${(income - expenses):,.2f}")

        st.write("---")

        # Category and Timeline charts
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Expenses by Category")
            df_exp = df_fin[df_fin["transaction_type"] == "Expense"]
            if df_exp.empty:
                st.info("No expenses recorded.")
            else:
                fig_exp = create_pie_chart(df_exp, "category", "amount", "Expense Category Share")
                st.plotly_chart(fig_exp, use_container_width=True)
                
        with col_c2:
            st.subheader("Monthly cash flow trend")
            # Group by month and type
            df_grouped = df_fin.groupby([df_fin['date'].dt.strftime('%Y-%m'), 'transaction_type'])['amount'].sum().unstack(fill_value=0.0).reset_index()
            
            import plotly.graph_objects as go
            fig_bar = go.Figure()
            if "Income" in df_grouped.columns:
                fig_bar.add_trace(go.Bar(x=df_grouped['date'], y=df_grouped['Income'], name='Income', marker_color=COLORS['success']))
            if "Expense" in df_grouped.columns:
                fig_bar.add_trace(go.Bar(x=df_grouped['date'], y=df_grouped['Expense'], name='Expense', marker_color=COLORS['danger']))
            if "Saving" in df_grouped.columns:
                fig_bar.add_trace(go.Bar(x=df_grouped['date'], y=df_grouped['Saving'], name='Savings', marker_color=COLORS['secondary']))
            
            fig_bar.update_layout(barmode='group')
            from frontend.utils.charts import apply_sleek_theme
            apply_sleek_theme(fig_bar, "Cash Flow Comparison")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.write("---")
        st.subheader("Recent Transactions")
        
        # Show table of transactions with deletion capability
        for idx, row in df_fin.iterrows():
            t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([1, 1, 2, 1, 1])
            with t_col1:
                st.write(row['date'].strftime('%Y-%m-%d'))
            with t_col2:
                # Color code type
                color = "green" if row['transaction_type'] == "Income" else "red" if row['transaction_type'] == "Expense" else "blue"
                st.markdown(f"<span style='color:{color}; font-weight:bold;'>{row['transaction_type']}</span>", unsafe_allow_html=True)
            with t_col3:
                st.write(f"**{row['category']}**: {row['description'] or ''}")
            with t_col4:
                st.write(f"${row['amount']:,.2f}")
            with t_col5:
                if st.button("🗑️ Delete", key=f"del_{row['id']}"):
                    try:
                        api_client.delete_finance(int(row['id']))
                        st.success("Deleted transaction!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting: {e}")

# ==================== TAB 2: ADD TRANSACTION MANUAL ====================
with tab2:
    st.subheader("Log Single Transaction")
    
    m_date = st.date_input("Transaction Date", date.today(), key="man_date")
    m_type = st.selectbox("Transaction Type", ["Expense", "Income", "Saving"], key="man_type")
    
    # Common categories auto-suggest
    categories = ["Food & Dining", "Rent & Housing", "Salary", "Investment / Stocks", "Entertainment", "Transport", "Utilities", "Health & Fitness", "Others"]
    m_category = st.selectbox("Category", categories, key="man_cat")
    # Allow custom category override
    custom_cat = st.text_input("Or write a custom category (overrides select box)", "", key="man_custom_cat")
    
    m_amount = st.number_input("Amount ($)", min_value=0.01, value=10.0, step=1.0, key="man_amount")
    m_description = st.text_input("Description", "", placeholder="e.g. Grocery shopping, salary payout...", key="man_desc")

    if st.button("Save Transaction", use_container_width=True):
        final_category = custom_cat.strip() if custom_cat.strip() else m_category
        payload = {
            "date": m_date.isoformat(),
            "transaction_type": m_type,
            "category": final_category,
            "amount": float(m_amount),
            "description": m_description.strip() or None
        }
        try:
            api_client.create_finance(payload)
            st.success("🎉 Transaction successfully added!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to add transaction: {e}")

# ==================== TAB 3: CSV IMPORT BANK STATEMENTS ====================
with tab3:
    st.subheader("Flexible CSV Import Mapper")
    st.write(
        "Upload a bank statement CSV file. You can map which columns represent Date, Amount, Description, and Category. We'll handle the rest."
    )

    uploaded_file = st.file_uploader("Upload Bank Statement CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Read first few lines or full df
            df_csv = pd.read_csv(uploaded_file)
            st.write("### Preview of uploaded data")
            st.dataframe(df_csv.head(5))

            columns = list(df_csv.columns)
            
            st.write("### Map Columns to Database Schema")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                date_col = st.selectbox("Date Column", columns, index=0 if len(columns) > 0 else 0)
            with col_m2:
                amount_col = st.selectbox("Amount Column", columns, index=1 if len(columns) > 1 else 0)
            with col_m3:
                desc_col = st.selectbox("Description Column", columns, index=2 if len(columns) > 2 else 0)
            with col_m4:
                cat_col = st.selectbox("Category Column (Optional)", ["None"] + columns, index=0)

            st.write("### Import Logic Settings")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                default_type = st.selectbox("Default Transaction Type (If cannot be deduced)", ["Expense", "Income", "Saving"])
            with col_s2:
                deduce_from_amount = st.checkbox("Deduce type from sign of Amount (Negative = Expense, Positive = Income)", value=True)

            # Map categories dictionary optionally
            st.write("---")
            if st.button("Parse and Preview Import", use_container_width=True):
                parsed_entries = []
                errors = []
                
                for idx, row in df_csv.iterrows():
                    try:
                        # Parse Date
                        raw_date = row[date_col]
                        # Try standard formats
                        parsed_date = None
                        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                            try:
                                parsed_date = datetime.strptime(str(raw_date).strip(), fmt).date()
                                break
                            except ValueError:
                                continue
                        
                        if not parsed_date:
                            # Try general pandas parser
                            parsed_date = pd.to_datetime(raw_date).date()
                            
                        # Parse Amount
                        raw_amount = float(str(row[amount_col]).replace('$', '').replace(',', '').strip())
                        
                        # Deduce transaction type
                        t_type = default_type
                        t_amount = abs(raw_amount)
                        
                        if deduce_from_amount:
                            if raw_amount < 0:
                                t_type = "Expense"
                            else:
                                t_type = "Income"
                        
                        # Parse category
                        t_category = "Imported"
                        if cat_col != "None":
                            t_category = str(row[cat_col]).strip() if pd.notna(row[cat_col]) else "Imported"
                        
                        # Description
                        t_desc = str(row[desc_col]).strip() if pd.notna(row[desc_col]) else ""
                        
                        parsed_entries.append({
                            "date": parsed_date,
                            "transaction_type": t_type,
                            "category": t_category,
                            "amount": t_amount,
                            "description": t_desc
                        })
                    except Exception as e:
                        errors.append(f"Row {idx+2}: {str(e)}")

                if errors:
                    st.warning(f"Skipped {len(errors)} rows due to parsing errors. Example: {errors[0]}")
                
                if parsed_entries:
                    st.success(f"Parsed {len(parsed_entries)} transactions successfully!")
                    df_preview = pd.DataFrame(parsed_entries)
                    st.dataframe(df_preview)
                    
                    # Store parsed list in session state for final confirmation
                    st.session_state.parsed_entries = parsed_entries
                else:
                    st.error("No transactions could be parsed. Check column mappings and date formats.")

            if "parsed_entries" in st.session_state and st.session_state.parsed_entries:
                st.write("---")
                if st.button("🚀 Confirm and Commit All to Database", use_container_width=True):
                    # Convert dates to string ISO format for JSON post
                    final_payload = []
                    for e in st.session_state.parsed_entries:
                        final_payload.append({
                            "date": e["date"].isoformat() if hasattr(e["date"], "isoformat") else e["date"],
                            "transaction_type": e["transaction_type"],
                            "category": e["category"],
                            "amount": float(e["amount"]),
                            "description": e["description"]
                        })
                    
                    try:
                        api_client.create_bulk_finances(final_payload)
                        st.success(f"Successfully imported {len(final_payload)} transactions!")
                        del st.session_state.parsed_entries
                        st.rerun()
                    except Exception as e:
                        st.error(f"Bulk transaction submission failed: {e}")
        except Exception as e:
            st.error(f"File reading error: {e}")
