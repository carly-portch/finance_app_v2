import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import date

st.title("Plan Your Future Together")
st.write("This tool helps you and your partner estimate your retirement savings and manage joint medium- and long-term goals.")
st.write("To get started, please fill out the fields below. You can add any medium- or long-term goals you both want to save for, such as a down payment on a house, children's education, or a dream vacation. Specify your goal either by entering the target year for achieving it or by providing your desired monthly contribution, and we’ll calculate when the goal will be reached. Once you've set a goal, click 'Add goal to timeline,' and it will appear in the timeline below. If you wish to remove a goal, use the left-side panel.")

# Initialize variables
current_year = date.today().year

# Input fields for retirement calculation
retirement_year = st.number_input("Enter the year you both plan to retire", min_value=current_year + 1)
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
                target_year = current_year + int(np.ceil(months_to_goal / 12))
            else:
                target_year = current_year + int(goal_amount / contribution_amount // 12)
    elif goal_type == "Target Year":
        target_year = st.number_input("Target year to reach this goal (yyyy)", min_value=current_year)
        contribution_amount = None

    # Add goal button
    if st.button("Add goal to timeline"):
        if goal_name and goal_amount > 0:
            if goal_type == "Monthly Contribution":
                target_year = int(target_year)
            elif goal_type == "Target Year":
                months_to_goal = 12 * (target_year - current_year)
                rate_of_return_monthly = interest_rate / 100 / 12
                if rate_of_return_monthly > 0:
                    monthly_contribution = goal_amount * rate_of_return_monthly / ((1 + rate_of_return_monthly) ** months_to_goal - 1)
                else:
                    monthly_contribution = goal_amount / months_to_goal

            # Append goal to session state
            st.session_state.goals.append({
                'goal_name': goal_name,
                'goal_amount': goal_amount,
                'monthly_contribution': contribution_amount if contribution_amount else monthly_contribution,
                'target_year': target_year
            })

            st.success(f"Goal '{goal_name}' added successfully.")
        else:
            st.error("Please enter a valid goal name and amount.")

# Function to calculate retirement net worth without goals
def calculate_retirement_net_worth_without_goals():
    monthly_savings = monthly_income - monthly_expenses
    months_to_retirement = (retirement_year - current_year) * 12
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

    months_to_retirement = (retirement_year - current_year) * 12
    rate_of_return_monthly = rate_of_return / 100 / 12

    if rate_of_return_monthly > 0:
        retirement_net_worth = remaining_contributions * ((1 + rate_of_return_monthly) ** months_to_retirement - 1) / rate_of_return_monthly
    else:
        retirement_net_worth = remaining_contributions * months_to_retirement

    return retirement_net_worth

# Plot timeline
def plot_timeline(snapshot_year=None):
    current_year = date.today().year
    
    # Create timeline data
    timeline_data = {
        'Year': [current_year, retirement_year] + [goal['target_year'] for goal in st.session_state.goals],
        'Event': ['Current Year', 'Retirement Year'] + [goal['goal_name'] for goal in st.session_state.goals],
        'Text': [
            f"<b>Current Year:</b> {current_year}<br><b>Combined Monthly Income:</b> ${monthly_income:,.2f}<br><b>Monthly Expenses:</b> ${monthly_expenses:,.2f}<br><b>Amount Going Towards Retirement:</b> ${monthly_income - monthly_expenses - sum(goal['monthly_contribution'] for goal in st.session_state.goals):,.2f}",
            f"<b>Retirement Year:</b> {retirement_year}<br><b>Net Worth at Retirement:</b> ${calculate_retirement_net_worth_with_goals():,.2f}"
        ] + [
            f"<b>Goal:</b> {goal['goal_name']}<br><b>Amount:</b> ${goal['goal_amount']:.2f}<br><b>Monthly Contribution:</b> ${goal['monthly_contribution']:.2f}"
            for goal in st.session_state.goals
        ]
    }

    timeline_df = pd.DataFrame(timeline_data)

    # Create the figure
    fig = go.Figure()
    
    # Add red dots for current and retirement years and goals
    fig.add_trace(go.Scatter(
        x=[current_year, retirement_year] + [goal['target_year'] for goal in st.session_state.goals], 
        y=[0] * (2 + len(st.session_state.goals)), 
        mode='markers+text', 
        marker=dict(size=12, color='red', line=dict(width=2, color='black')), 
        text=['Current Year', 'Retirement Year'] + [goal['goal_name'] for goal in st.session_state.goals], 
        textposition='top center', 
        hoverinfo='text', 
        hovertext=timeline_df['Text']
    ))
    
    # Add line connecting the red dots
    fig.add_trace(go.Scatter(
        x=[current_year, retirement_year] + [goal['target_year'] for goal in st.session_state.goals], 
        y=[0] * (2 + len(st.session_state.goals)), 
        mode='lines', 
        line=dict(color='red', width=2)
    ))

    # Add a vertical line for the selected snapshot year if provided
    if snapshot_year is not None:
        fig.add_vline(x=snapshot_year, line_color="blue", line_width=2, annotation_text="Snapshot Year", annotation_position="top right")
    
    # Update layout
    fig.update_layout(
        title="Joint Life Timeline",
        xaxis_title='Year',
        yaxis=dict(visible=False),
        xaxis=dict(
            tickmode='array',
            tickvals=[current_year, retirement_year] + [goal['target_year'] for goal in st.session_state.goals],
            ticktext=[f"{current_year}", f"{retirement_year}"] + [f"{goal['target_year']}" for goal in st.session_state.goals]
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

# Calculate and display the financial snapshot
snapshot_year = st.number_input("Enter a year to view financial snapshot", min_value=current_year, max_value=retirement_year)

# Plot timeline without the snapshot line initially
plot_timeline()

if st.button("Show Snapshot"):
    st.markdown("### Financial Snapshot")
    
    # Calculate contributions and retirement savings
    contributions = monthly_income - monthly_expenses
    for goal in st.session_state.goals:
        contributions -= goal['monthly_contribution']
    
    retirement_net_worth = calculate_retirement_net_worth_with_goals()
    
    # Create a summary table
    st.write("#### Current Monthly Income")
    st.write(f"${monthly_income:,.2f}")

    st.write("#### Current Monthly Expenses")
    st.write(f"${monthly_expenses:,.2f}")

    st.write("#### Contributions")
    st.write("**To Goals:**")
    for goal in st.session_state.goals:
        st.write(f"- {goal['goal_name']}: ${goal['monthly_contribution']:.2f}")

    st.write(f"**To Retirement:** ${contributions:.2f}")

    st.write("#### Goals")
    for goal in st.session_state.goals:
        saved_amount = min(goal['goal_amount'], goal['monthly_contribution'] * (snapshot_year - current_year) * 12)
        progress = saved_amount / goal['goal_amount'] if goal['goal_amount'] > 0 else 0
        st.write(f"- {goal['goal_name']}: ${saved_amount:.2f} saved ({progress:.0%} complete)")
        st.progress(progress)

    st.write("#### Retirement Savings")
    st.write(f"${retirement_net_worth:,.2f}")

    # Plot timeline with the selected snapshot year
    plot_timeline(snapshot_year)
