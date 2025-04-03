import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import uuid
import os

# Define the CSV file path
LOANS_CSV_PATH = "loans_database.csv"

def calculate_interest(amount, rate, start_date, end_date):
    """Calculate interest for a given amount, rate, and time period."""
    time_period = (end_date - start_date).days
    monthly_interest = (amount * rate / 100) * (time_period / 30)
    return round(monthly_interest, 2), time_period

def load_loans_from_csv():
    """Load loans from CSV file if it exists."""
    if os.path.exists(LOANS_CSV_PATH):
        try:
            loans_df = pd.read_csv(LOANS_CSV_PATH)
            
            # Convert date strings back to datetime objects for calculations
            if not loans_df.empty:
                loans_df["start_date_dt"] = pd.to_datetime(loans_df["start_date"])
                loans_df["end_date_dt"] = pd.to_datetime(loans_df["end_date"])
                
                # Convert DataFrame to list of dictionaries
                loans = loans_df.to_dict('records')
                return loans
        except Exception as e:
            st.error(f"Error loading loans: {e}")
    
    return []

def save_loans_to_csv(loans):
    """Save loans to CSV file."""
    if loans:
        try:
            loans_df = pd.DataFrame(loans)
            loans_df.to_csv(LOANS_CSV_PATH, index=False)
            return True
        except Exception as e:
            st.error(f"Error saving loans: {e}")
            return False
    return False

def main():
    st.set_page_config(page_title="Loan Tracker", layout="wide")
    
    st.title("Loan Tracker Application")
    st.write("Track loans with varying interest rates and generate reports.")
    
    # Initialize session state for tracking loans
    if 'loans' not in st.session_state:
        st.session_state.loans = load_loans_from_csv()
    
    # Track if we're editing a loan or adding a new one
    if 'editing_loan' not in st.session_state:
        st.session_state.editing_loan = None
        
    # Loan entry form
    with st.form("loan_entry_form"):
        if st.session_state.editing_loan:
            st.subheader(f"Edit Loan for {st.session_state.editing_loan['person']}")
            loan_to_edit = st.session_state.editing_loan
            form_id = loan_to_edit['id']
        else:
            st.subheader("Add New Loan")
            form_id = None
            loan_to_edit = {"person": "", "amount": 10000.0, "rate": 1.5, 
                           "start_date": datetime.now().strftime('%Y-%m-%d'), 
                           "end_date": datetime.now().strftime('%Y-%m-%d')}
        
        col1, col2 = st.columns(2)
        
        with col1:
            person_name = st.text_input("Person's Name", value=loan_to_edit["person"])
            loan_amount = st.number_input("Loan Amount", min_value=0.0, value=float(loan_to_edit["amount"]), step=1000.0)
            interest_rate = st.number_input("Monthly Interest Rate (%)", min_value=0.0, max_value=10.0, 
                                          value=float(loan_to_edit["rate"]), step=0.1)
        
        with col2:
            loan_date = st.date_input("Loan Date", value=pd.to_datetime(loan_to_edit["start_date"]))
            end_date = st.date_input("End Date (for calculation)", value=pd.to_datetime(loan_to_edit["end_date"]))
            st.write("Use today's date for ongoing loans")
        
        if st.session_state.editing_loan:
            submit_button = st.form_submit_button("Update Loan")
        else:
            submit_button = st.form_submit_button("Add Loan")
        
        if submit_button:
            if person_name and loan_amount > 0:
                # Convert to datetime objects first, then to strings with a specific format
                start_date_str = pd.to_datetime(loan_date).strftime('%Y-%m-%d')
                end_date_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')
                
                # Create datetime objects for calculation
                start_date_dt = pd.to_datetime(start_date_str)
                end_date_dt = pd.to_datetime(end_date_str)
                
                # Calculate derived values
                interest, days = calculate_interest(
                    loan_amount, 
                    interest_rate, 
                    start_date_dt, 
                    end_date_dt
                )
                
                # Create/update loan info
                loan_info = {
                    "id": form_id if form_id else str(uuid.uuid4()),  # Use existing ID or generate new one
                    "person": person_name,
                    "amount": loan_amount,
                    "rate": interest_rate,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "start_date_dt": start_date_dt,
                    "end_date_dt": end_date_dt,
                    "days": days,
                    "interest": interest,
                    "total": loan_amount + interest
                }
                
                if st.session_state.editing_loan:
                    # Find and replace the existing loan
                    for i, loan in enumerate(st.session_state.loans):
                        if loan['id'] == form_id:
                            st.session_state.loans[i] = loan_info
                            save_loans_to_csv(st.session_state.loans)
                            st.success(f"Loan to {person_name} updated successfully!")
                            break
                    st.session_state.editing_loan = None  # Reset editing state
                else:
                    # Add new loan
                    st.session_state.loans.append(loan_info)
                    save_loans_to_csv(st.session_state.loans)
                    st.success(f"Loan of {loan_amount} to {person_name} added successfully!")
            else:
                st.error("Please fill in all required fields")
    
    # Cancel editing button (outside the form)
    if st.session_state.editing_loan:
        if st.button("Cancel Editing"):
            st.session_state.editing_loan = None
            st.rerun()
    
    # Display current loans
    if st.session_state.loans:
        st.subheader("Current Loans")
        
        loans_df = pd.DataFrame(st.session_state.loans)
        
        # Use only the columns we need for display
        display_columns = [
            "person", "amount", "rate", "start_date", 
            "end_date", "days", "interest", "total"
        ]
        
        # Make sure we have all required columns
        for col in display_columns:
            if col not in loans_df.columns:
                if col == "days" or col == "interest" or col == "total":
                    loans_df[col] = 0
                else:
                    loans_df[col] = ""
        
        # Add delete and edit buttons for each loan
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.dataframe(loans_df[display_columns])
        
        with col2:
            st.subheader("Edit Loans")
            
            # Create edit buttons for individual loans
            for loan in st.session_state.loans:
                if st.button(f"Edit {loan['person']}", key=f"edit_{loan['id']}"):
                    st.session_state.editing_loan = loan
                    st.rerun()
        
        with col3:
            st.subheader("Delete Loans")
            
            # Create delete buttons for individual loans
            for index, loan in enumerate(st.session_state.loans):
                if st.button(f"Delete {loan['person']}", key=f"del_{loan['id']}"):
                    del st.session_state.loans[index]
                    save_loans_to_csv(st.session_state.loans)
                    st.success("Loan deleted successfully!")
                    st.rerun()
        
        # Option to remove all loans
        if st.button("Clear All Loans"):
            st.session_state.loans = []
            save_loans_to_csv(st.session_state.loans)
            st.success("All loans cleared!")
            st.rerun()
        
        # Generate Combined Report Button
        if st.button("Generate Combined Report"):
            st.subheader("Combined Loan Report")
            
            # Update calculated fields for all loans
            for i, loan in enumerate(st.session_state.loans):
                interest, days = calculate_interest(
                    loan["amount"], 
                    loan["rate"], 
                    loan["start_date_dt"], 
                    pd.to_datetime(datetime.now().strftime('%Y-%m-%d'))  # Use current date for latest calculations
                )
                st.session_state.loans[i]["days"] = days
                st.session_state.loans[i]["interest"] = interest
                st.session_state.loans[i]["total"] = loan["amount"] + interest
            
            # Save updated calculations to CSV
            save_loans_to_csv(st.session_state.loans)
            
            # Create DataFrame from updated loans
            loans_df = pd.DataFrame(st.session_state.loans)
            
            # Summary statistics
            total_amount_lent = loans_df["amount"].sum()
            total_interest = loans_df["interest"].sum()
            total_receivable = loans_df["total"].sum()
            avg_interest_rate = loans_df["rate"].mean()
            total_loans = len(loans_df)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Loans", f"{total_loans}")
            with col2:
                st.metric("Total Amount Lent", f"₹{total_amount_lent:,.2f}")
            with col3:
                st.metric("Total Interest", f"₹{total_interest:,.2f}")
            with col4:
                st.metric("Total Receivable", f"₹{total_receivable:,.2f}")
            
            st.write(f"Average Interest Rate: {avg_interest_rate:.2f}% per month")
            
            # Breakdown by person
            st.subheader("Breakdown by Person")
            person_summary = loans_df.groupby("person").agg({
                "amount": "sum",
                "interest": "sum",
                "total": "sum"
            }).reset_index()
            
            person_summary["percentage"] = (person_summary["total"] / person_summary["total"].sum() * 100).round(2)
            person_summary.columns = ["Person", "Amount Lent", "Interest", "Total Receivable", "Percentage (%)"]
            
            st.dataframe(person_summary)
            
            # Visualizations for combined report
            st.subheader("Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart for amount distribution by person
                fig_pie = px.pie(
                    person_summary,
                    values="Total Receivable",
                    names="Person",
                    title="Amount Receivable by Person (%)",
                    hover_data=["Percentage (%)"]
                )
                st.plotly_chart(fig_pie)
            
            with col2:
                # Stacked bar chart showing principal vs interest by person
                fig_bar = go.Figure()
                for person in person_summary["Person"]:
                    person_data = person_summary[person_summary["Person"] == person]
                    principal = person_data["Amount Lent"].values[0]
                    interest = person_data["Interest"].values[0]
                    
                    fig_bar.add_trace(go.Bar(
                        name=f"{person} - Principal",
                        x=[person],
                        y=[principal],
                        marker_color='blue'
                    ))
                    
                    fig_bar.add_trace(go.Bar(
                        name=f"{person} - Interest",
                        x=[person],
                        y=[interest],
                        marker_color='red'
                    ))
                
                fig_bar.update_layout(
                    title="Principal vs Interest by Person",
                    barmode='stack'
                )
                st.plotly_chart(fig_bar)
            
            # Loan distribution by month
            loans_by_month = loans_df.copy()
            loans_by_month["month"] = pd.to_datetime(loans_by_month["start_date"]).dt.strftime('%b %Y')
            monthly_summary = loans_by_month.groupby("month").agg({
                "amount": "sum",
                "interest": "sum"
            }).reset_index()
            
            fig_monthly = px.bar(
                monthly_summary,
                x="month",
                y=["amount", "interest"],
                title="Monthly Loan Distribution",
                labels={"value": "Amount", "month": "Month"},
                barmode="stack"
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
            
            # Download option for combined report
            st.download_button(
                "Download Combined Report as CSV",
                loans_df[display_columns].to_csv(index=False).encode('utf-8'),
                f"combined_loan_report_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key="download-combined-csv"
            )
        
        # Individual report section
        st.subheader("Generate Individual Report")
        
        # Group by person
        people = loans_df["person"].unique()
        selected_person = st.selectbox("Select Person for Report", people)
        
        if st.button("Generate Individual Report"):
            person_loans = loans_df[loans_df["person"] == selected_person]
            
            # Calculate summary statistics
            total_amount_lent = person_loans["amount"].sum()
            total_interest = person_loans["interest"].sum()
            total_receivable = person_loans["total"].sum()
            avg_interest_rate = person_loans["rate"].mean()
            
            # Create report
            st.subheader(f"Loan Report for {selected_person}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Amount Lent", f"₹{total_amount_lent:,.2f}")
            with col2:
                st.metric("Total Interest", f"₹{total_interest:,.2f}")
            with col3:
                st.metric("Total Receivable", f"₹{total_receivable:,.2f}")
            
            st.write(f"Average Interest Rate: {avg_interest_rate:.2f}% per month")
            
            # Detailed breakdown
            st.subheader("Detailed Breakdown")
            st.dataframe(person_loans[display_columns])
            
            # Visualizations
            st.subheader("Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Create pie chart
                fig_pie = px.pie(
                    values=[total_amount_lent, total_interest],
                    names=["Principal", "Interest"],
                    title="Principal vs Interest"
                )
                st.plotly_chart(fig_pie)
            
            with col2:
                # Create bar chart for individual loans
                fig_bar = px.bar(
                    person_loans,
                    x="start_date",
                    y=["amount", "interest"],
                    title="Loans and Interest by Date",
                    labels={"value": "Amount", "start_date": "Loan Date"},
                    barmode="stack"
                )
                st.plotly_chart(fig_bar)
            
            # Export option
            st.download_button(
                "Download Report as CSV",
                person_loans[display_columns].to_csv(index=False).encode('utf-8'),
                f"loan_report_{selected_person}_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key="download-csv"
            )

if __name__ == "__main__":
    main()