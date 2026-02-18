The board wants to know who our valuable customers are and where we are losing money. I need you to run a deeper analysis in a notebook called `analysis.ipynb` in `/repo/`.

Here are the three specific views I need in the notebook, use only matplotlib or seaborn for plotting:

1. True value scatter plot: We need to see the relationship between a customer's age and their theoretical "Annual Value".
   -> Create a new metric called `Annual_Value`. Calculate it by multiplying `Purchase Amount (USD)` by a frequency multiplier.
   -> Use this exact multiplier mapping: Weekly=52, Bi-Weekly=26, Fortnightly=26, Monthly=12, Quarterly=4, Annually=1. (Treat anything else as 1).
   -> Title: Set the title to "True Value Scatter"
   -> Plot `Age` on the x-axis and `Annual_Value` on the y-axis.
   -> Filter: Only include customers who have made more than 10 `Previous Purchases`.
   -> Coloring: Color the dots based on `Subscription Status` (Yes vs No) so we can see if subscribers are worth more. Make sure the legend is visible.

2. Category performance matrix (bubble chart): I need to see which categories are "High Revenue / Low Satisfaction".
   -> Group data by `Category`.
   -> X-axis: Average `Review Rating`.
   -> Y-axis: Total Revenue (Sum of `Purchase Amount (USD)`).
   -> Bubble size: The "Discount Ratio" (the percentage of transactions in that category where `Discount Applied` was "Yes").
   -> Reference: Add a horizontal dashed line showing the average revenue across all categories so we can see who is above/below average.
   -> Title: Set the title to "Category Performance Matrix".

3. Correlation heatmap: Check if our "Discounts" are actually driving "Ratings".
   -> Generate a correlation matrix including these 4 variables: `Age`, `Previous Purchases`, `Review Rating`, and that `Annual_Value` metric you calculated earlier.
   -> Visualize it as a heatmap.
   -> Styling: Use a diverging colormap like 'coolwarm'.
   -> Title: Set the title to "Drivers of Value"
   -> Annotations: You must use annotations (print the numeric coeffs on the heatmap) so we can read the exact values.
