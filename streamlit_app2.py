import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import date

st.title("Plan Your Future Together")
st.write("This tool helps you and your partner estimate your retirement savings and manage joint medium- and long-term goals.")
st.write("To get started, please fill out the fields below. You can add any medium- or long-term goals you both want to save for, such as a down payment on a house, children's education, or a dream vacation. Specify your goal either by entering the target year for achieving it or by providing your desired monthly contribution, and we’ll calculate when the goal will be reached. Once you've set a goal, click 'Add goal to timeline,' and it will appear in the timeline below. If you wish to remove a goal, use the left-side panel.")

# Input fields for retirement calculation
retirement_year = st.number_input("Enter the year you both plan to retire", min_value=date.today().year + 1)
monthly_income = st.number_input("Enter your combined monthly income after tax", min_value=0.0)
monthly_expenses = st.number_input("Enter your combined monthly expenses", min_value=0.0)
rate_of_return = st.number_input("Rate of return or interest rate (%) for retirement funds", min_value=0.0, max_value=100.0, value=5.0)

# Initialize goal list
if 'goals' not in st.session_state:
    st.session_state.goals = []

# Display goal addition dropdown
with st.expander("Add a Goal"):
    goal_name = st.text_input("Name of goal")
    goal_amount = st.number_input("Goal amount", min_value=0.0)
    interest_rate = st.number_input("Rate of return or interest rate (%)", min_value=0.0, max_value=100.0, value=5.0)
    goal_type = st.radio("Select how you want to calculate your goal", ["Target Year", "Monthly Contribution"])

    if goal_type == "Monthly Contribution":
        contribution_amount = st.number_input("Monthly contribution towards this goal", min_value=0.0)
        if contribution_amount > 0 and goal_amount > 0:
            rate_of_return_monthly = interest_rate / 100 / 12
            if rate_of_return_monthly > 0:
                months_to_goal = np.log(1 + (goal_amount * rate_of_return_monthly) / contribution_amount) / np.log(1 + rate_of_return_monthly)
                target_year = date.today().year + int(np.ceil(months_to_goal / 12))
            else:
                target_year = date.today().year + int(goal_amount / contribution_amount // 12)
    elif goal_type == "Target Year":
        target_year = st.number_input("Target year to reach this goal (yyyy)", min_value=date.today().year)
        contribution_amount = None

    # Add goal button
    if st.button("Add goal to timeline"):
        if goal_name and goal_amount > 0:
            if goal_type == "Monthly Contribution":
                target_year = int(target_year)
            elif goal_type == "Target Year":
                months_to_goal = 12 * (target_year - date.today().year)
                rate_of_return_monthly = interest_rate / 100 / 12
                if rate_of_return_monthly > 0:
                    monthly_contribution = goal_amount * rate_of_return_monthly / ((1 + rate_of_return_monthly) ** months_to_goal - 1)
                else:
                    monthly_contribution = goal_amount / months_to_goal
            else:
                monthly_contribution = 0

            # Append goal to session state
            st.session_state.goals.append({
                'goal_name': goal_name,
                'goal_amount': goal_amount,
                'monthly_contribution': contribution_amount if contribution_amount else monthly_contribution,
                'target_year': target_year
            })

            st.success(f"Goal '{goal_name}' added successfully.")
            st.session_state.plot_updated = False  # Flag to update the plot
        else:
            st.error("Please enter a valid goal name and amount.")

# Function to calculate retirement net worth without goals
def calculate_retirement_net_worth_without_goals():
    monthly_savings = monthly_income - monthly_expenses
    months_to_retirement = (retirement_year - date.today().year) * 12
    rate_of_return_monthly = rate_of_return / 100 / 12

    if rate_of_return_monthly > 0:
        retirement_net_worth = monthly_savings * ((1 + rate_of_return_monthly) ** months_to_retirement - 1) / rate_of_return_monthly
    else:
        retirement_net_worth = monthly_savings * months_to_retirement

    return retirement_net_worth

# Function to calculate retirement net worth with goals
def calculate_retirement_net_worth_with_goals():
    remaining_contributions = monthly_income - monthly_expenses
    for goal in st.session_state.goals:
        remaining_contributions -= goal['monthly_contribution']

    months_to_retirement = (retirement_year - date.today().year) * 12
    rate_of_return_monthly = rate_of_return / 100 / 12

    if rate_of_return_monthly > 0:
        retirement_net_worth = remaining_contributions * ((1 + rate_of_return_monthly) ** months_to_retirement - 1) / rate_of_return_monthly
    else:
        retirement_net_worth = remaining_contributions * months_to_retirement

    return retirement_net_worth

# Plot timeline
def plot_timeline(snapshot_year=None):
    current_year = date.today().year
    timeline_years = [current_year, retirement_year] + [goal['target_year'] for goal in st.session_state.goals]
    timeline_events = ['Current Year', 'Retirement Year'] + [goal['goal_name'] for goal in st.session_state.goals]
    
    # Create the figure
    fig = go.Figure()
    
    # Add red dots for current and retirement years and goals
    fig.add_trace(go.Scatter(
        x=timeline_years, 
        y=[0] * len(timeline_years), 
        mode='markers+text', 
        marker=dict(size=12, color='red', line=dict(width=2, color='black')), 
        text=timeline_events, 
        textposition='top center', 
        hoverinfo='text', 
        hovertext=[f"<b>Year:</b> {year}<br><b>Goal:</b> {goal['goal_name']}<br><b>Monthly Contribution:</b> ${goal['monthly_contribution']:.2f}" for year, goal in zip(timeline_years[2:], st.session_state.goals)] + 
                   [f"<b>Year:</b> {current_year}<br><b>Income:</b> ${monthly_income:,.2f}<br><b>Expenses:</b> ${monthly_expenses:,.2f}<br><b>Amount for Retirement:</b> ${monthly_income - monthly_expenses - sum(goal['monthly_contribution'] for goal in st.session_state.goals):,.2f}",
                    f"<b>Year:</b> {retirement_year}<br><b>Net Worth at Retirement:</b> ${calculate_retirement_net_worth_with_goals():,.2f}"]
    ))
    
    # Add vertical line for snapshot year
    if snapshot_year:
        fig.add_trace(go.Scatter(
            x=[snapshot_year, snapshot_year], 
            y=[-0.5, 0.5], 
            mode='lines', 
            line=dict(color='blue', width=2, dash='dash'), 
            name='Snapshot Year'
        ))

    # Add line connecting the red dots
    fig.add_trace(go.Scatter(
        x=timeline_years, 
        y=[0] * len(timeline_years), 
        mode='lines', 
        line=dict(color='red', width=2)
    ))
    
    # Update layout
    fig.update_layout(
        title="Joint Life Timeline",
        xaxis_title='Year',
        yaxis=dict(visible=False),
        xaxis=dict(
            tickmode='array',
            tickvals=timeline_years,
            ticktext=[f"{year}" for year in timeline_years]
        ),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

# Display existing goals in the sidebar
st.sidebar.header("Existing Goals")
goal_to_remove = st.sidebar.selectbox("Select a goal to remove", [""] + [goal['goal_name'] for goal in st.session_state.goals])

if st.sidebar.button("Remove Goal"):
    if goal_to_remove:
        st.session_state.goals = [goal for goal in st.session_state.goals if goal['goal_name'] != goal_to_remove]
        st.sidebar.success(f"Goal '{goal_to_remove}' removed successfully.")
        st.session_state.plot_updated = False

# Calculate and display net worth
net_worth = calculate_retirement_net_worth_with_goals()
st.header("Retirement Net Worth")
st.write(f"Your estimated net worth at retirement is **${net_worth:,.2f}**.")

# Display timeline
plot_timeline()

# Input field for selecting a year for financial snapshot
selected_year = st.number_input("Enter a year to view financial snapshot", min_value=date.today().year, max_value=retirement_year)

# Button to show snapshot
if st.button("Show Snapshot"):
    plot_timeline(snapshot_year=selected_year)

    # Function to calculate the snapshot of finances in a given year
    def calculate_financial_snapshot(year):
        monthly_savings = monthly_income - monthly_expenses
        goal_snapshots = {}
        total_goal_contributions = 0

        for goal in st.session_state.goals:
            years_remaining = goal['target_year'] - year
            if years_remaining >= 0:
                total_goal_contributions += goal['monthly_contribution'] * 12
                goal_snapshots[goal['goal_name']] = {
                    'amount_saved': min(total_goal_contributions, goal['goal_amount']),
                    'progress': min(total_goal_contributions / goal['goal_amount'] * 100, 100)
                }
        
        current_retirement_savings = calculate_retirement_net_worth_without_goals()
        return {
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'goal_snapshots': goal_snapshots,
            'retirement_savings': current_retirement_savings
        }

    snapshot_data = calculate_financial_snapshot(selected_year)

    # Display financial snapshot
    st.subheader("Financial Snapshot")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Current Monthly Contributions:**")
        st.write(f"Income: ${snapshot_data['monthly_income']:.2f}")
        st.write(f"Expenses: ${snapshot_data['monthly_expenses']:.2f}")

    with col2:
        st.write("**Goals Progress:**")
        for goal, details in snapshot_data['goal_snapshots'].items():
            st.write(f"{goal}: ${details['amount_saved']} ({details['progress']:.2f}%)")
            st.progress(details['progress'] / 100)

    st.subheader("Retirement Savings")
    st.write(f"Current Retirement Savings: ${snapshot_data['retirement_savings']:.2f}")

