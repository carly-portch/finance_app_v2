import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import date

st.title("Design Your Dream Life as a Couple")
st.write("This tool helps you estimate your joint retirement savings and manage medium and long-term goals as a couple.")
st.write("""
    To get started, please fill out the fields below. You can add any medium- or long-term goals you want to save for, such as a house down payment, child's college fund, or a wedding.
    You can specify your goal either by entering the target date for achieving it or by providing your desired monthly contribution; we’ll calculate the year you can expect to reach that goal. 
    Once you’ve set your goal, click 'Add goal to timeline,' and it will appear in the life timeline at the bottom of the page.
    If you wish to remove a goal, you can delete it using the left-side panel. Your estimated retirement savings is based on the assumption that all money leftover after you pay for monthly expenses and goals will be put towards retirement. 
    Once a goal is reached, the contribution money will be redirected towards retirement savings.
""")

# Input fields for retirement calculation
retirement_year = st.number_input("Enter the year you both plan to retire", min_value=date.today().year + 1)
monthly_income = st.number_input("Enter your joint monthly income after tax", min_value=0.0)
monthly_expenses = st.number_input("Enter your joint monthly expenses", min_value=0.0)
rate_of_return = st.number_input("Rate of return or interest rate (%) for retirement funds", min_value=0.0, max_value=100.0, value=5.0)

st.write("""
    Note: The rate of return refers to the growth of your money based on where it's invested. 
    For instance, if you plan to invest your retirement savings in the stock market, the average rate of return is typically around 6-7%. 
    For a high-interest savings account, the interest rate usually ranges from 2-5%. However, if you're aware of the specific interest rate offered by your bank, use that figure.
""")

# Initialize goal list
if 'goals' not in st.session_state:
    st.session_state.goals = []

# Display goal addition dropdown
with st.expander("Add a Goal"):
    goal_name = st.text_input("Name of goal")
    goal_amount = st.number_input("Goal amount", min_value=0.0)
    interest_rate = st.number_input("Rate of return or interest rate (%) for the goal", min_value=0.0, max_value=100.0, value=5.0)
    goal_type = st.radio("Select how you want to calculate your goal", ["Target Date", "Monthly Contribution"])

    if goal_type == "Monthly Contribution":
        contribution_amount = st.number_input("Monthly contribution towards this goal", min_value=0.0)
        target_year = None
        if contribution_amount > 0 and goal_amount > 0:
            rate_of_return_monthly = interest_rate / 100 / 12
            if rate_of_return_monthly > 0:
                months_to_goal = np.log(1 + (goal_amount * rate_of_return_monthly) / contribution_amount) / np.log(1 + rate_of_return_monthly)
                target_year = date.today().year + int(np.ceil(months_to_goal / 12))
            else:
                target_year = date.today().year + int(goal_amount / contribution_amount // 12)
    elif goal_type == "Target Date":
        target_year = st.number_input("Target year to reach this goal (yyyy)", min_value=date.today().year)
        contribution_amount = None

    if st.button("Add goal to timeline"):
        if goal_name and goal_amount > 0:
            if goal_type == "Monthly Contribution":
                target_year = int(target_year)
            elif goal_type == "Target Date":
                months_to_goal = 12 * (target_year - date.today().year)
                rate_of_return_monthly = interest_rate / 100 / 12
                if rate_of_return_monthly > 0:
                    monthly_contribution = goal_amount * rate_of_return_monthly / ((1 + rate_of_return_monthly) ** months_to_goal - 1)
                else:
                    monthly_contribution = goal_amount / months_to_goal
            else:
                monthly_contribution = 0

            st.session_state.goals.append({
                'goal_name': goal_name,
                'goal_amount': goal_amount,
                'monthly_contribution': contribution_amount if contribution_amount else monthly_contribution,
                'target_year': target_year
            })

            st.success(f"Goal '{goal_name}' added successfully.")
            st.session_state.plot_updated = False

# Function to calculate retirement net worth with dynamic goal contributions
def calculate_retirement_net_worth_with_goals_dynamic():
    total_years = retirement_year - date.today().year
    current_year = date.today().year
    
    # Initialize savings to total monthly income minus expenses
    remaining_savings = monthly_income - monthly_expenses
    
    # Sort goals by target year to calculate dynamically
    sorted_goals = sorted(st.session_state.goals, key=lambda g: g['target_year'])
    
    # Initialize the net worth accumulator
    retirement_net_worth = 0.0
    rate_of_return_monthly = rate_of_return / 100 / 12
    
    for year in range(current_year, retirement_year):
        monthly_contribution = remaining_savings
        
        # Subtract goal contributions for active goals this year
        for goal in sorted_goals:
            if year < goal['target_year']:
                monthly_contribution -= goal['monthly_contribution']  # Subtract active goal contribution

        # Add the amount going into retirement savings this year
        months_left_in_year = 12
        if rate_of_return_monthly > 0:
            retirement_net_worth += monthly_contribution * ((1 + rate_of_return_monthly) ** months_left_in_year - 1) / rate_of_return_monthly
        else:
            retirement_net_worth += monthly_contribution * months_left_in_year

        # After each goal is reached, add its contribution to retirement savings
        for goal in sorted_goals:
            if year >= goal['target_year']:
                remaining_savings += goal['monthly_contribution']  # Add back goal contribution to savings after goal is reached

    return retirement_net_worth

# Plot timeline
def plot_timeline():
    if 'plot_updated' in st.session_state and st.session_state.plot_updated:
        return
    
    today = date.today()
    current_year = today.year
    retirement_year_local = retirement_year
    
    timeline_data = {
        'Year': [current_year, retirement_year_local] + [goal['target_year'] for goal in st.session_state.goals],
        'Event': ['Current Year', 'Retirement Year'] + [goal['goal_name'] for goal in st.session_state.goals],
        'Text': [
            f"<b>Current Year:</b> {current_year}<br><b>Joint Monthly Income:</b> ${monthly_income:,.2f}<br><b>Joint Monthly Expenses:</b> ${monthly_expenses:,.2f}<br><b>Amount Going Towards Retirement:</b> ${monthly_income - monthly_expenses - sum(goal['monthly_contribution'] for goal in st.session_state.goals):,.2f}",
            f"<b>Retirement Year:</b> {retirement_year_local}<br><b>Net Worth at Retirement:</b> ${calculate_retirement_net_worth_with_goals_dynamic():,.2f}"
        ] + [
            f"<b>Goal:</b> {goal['goal_name']}<br><b>Amount:</b> ${goal['goal_amount']:.2f}<br><b>Monthly Contribution:</b> ${goal['monthly_contribution']:.2f}"
            for goal in st.session_state.goals
        ]
    }

    timeline_df = pd.DataFrame(timeline_data)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=[current_year, retirement_year_local] + [goal['target_year'] for goal in st.session_state.goals], 
        y=[0] * (2 + len(st.session_state.goals)), 
        mode='markers+text', 
        marker=dict(size=12, color='red', line=dict(width=2, color='black')), 
        text=['Current Year', 'Retirement Year'] + [goal['goal_name'] for goal in st.session_state.goals], 
        textposition='top center', 
        hoverinfo='text', 
        hovertext=timeline_df['Text']
    ))

    fig.add_trace(go.Scatter(
        x=[current_year, retirement_year_local] + [goal['target_year'] for goal in st.session_state.goals], 
        y=[0] * (2 + len(st.session_state.goals)), 
        mode='lines', 
        line=dict(color='red', width=2)
    ))

    fig.update_layout(
        title="Life Timeline",
        xaxis_title='Year',
        yaxis=dict(visible=False),
        xaxis=dict(
            tickmode='array',
            tickvals=[current_year, retirement_year_local] + [goal['target_year'] for goal in st.session_state.goals],
            ticktext=[f"{current_year}", f"{retirement_year_local}"] + [f"{goal['target_year']}" for goal in st.session_state.goals]
        ),
        showlegend=False
    )

    fig.update_traces(
        hovertemplate='<b>Year:</b> %{x}<br>%{hovertext}'
    )

    st.plotly_chart(fig)
    st.session_state.plot_updated = True

# Plot the timeline
plot_timeline()

# Calculate and display net worth
st.header("Retirement Net Worth")
net_worth = calculate_retirement_net_worth_with_goals_dynamic()
st.write(f"Your estimated net worth at retirement is **${net_worth:,.2f}**.")
