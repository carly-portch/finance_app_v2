# Function to calculate retirement net worth with goals, adjusting after goal is reached
def calculate_retirement_net_worth_with_goals():
    current_year = date.today().year
    total_retirement_savings = 0
    current_savings = 0
    rate_of_return_monthly = rate_of_return / 100 / 12
    
    # Loop through each year until retirement
    for year in range(current_year, retirement_year + 1):
        # Calculate how much should be contributed to retirement this year
        monthly_savings = monthly_income - monthly_expenses
        
        # Subtract goal contributions if the goal has not yet been reached
        for goal in st.session_state.goals:
            if year <= goal['target_year']:  # Only deduct contributions before the goal year
                monthly_savings -= goal['monthly_contribution']
        
        # Calculate monthly compound interest for the year
        if rate_of_return_monthly > 0:
            current_savings += monthly_savings * ((1 + rate_of_return_monthly) ** 12 - 1) / rate_of_return_monthly
        else:
            current_savings += monthly_savings * 12
        
        total_retirement_savings = current_savings

    return total_retirement_savings

# Update the function for displaying net worth at retirement
st.header("Retirement Net Worth")
net_worth = calculate_retirement_net_worth_with_goals()
st.write(f"Your estimated net worth at retirement is **${net_worth:,.2f}**.")

# Update the timeline text to show how savings change after goals are reached
timeline_data['Text'][1] = f"<b>Retirement Year:</b> {retirement_year}<br><b>Net Worth at Retirement:</b> ${net_worth:,.2f}"

# Ensure the plot is updated after any changes
st.session_state.plot_updated = False

# Re-plot the timeline
plot_timeline()
