import altair as alt
import pandas as pd

# Define common player graph values values
CATEGORY_ORDER = ['Player', 'Team', 'Opponents']
CATEGORY_COLORS = ['#0168c8', '#84C9FF', '#FFABAA']


def create_comparison_chart(data, category_col, value_col, title):
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X(f'{category_col}:N', sort=CATEGORY_ORDER, title=""),
        y=alt.Y(f'{value_col}:Q'),
        color=alt.Color(f'{category_col}:N', 
                        scale=alt.Scale(domain=CATEGORY_ORDER, range=CATEGORY_COLORS),
                        legend=None),
        tooltip=[category_col, value_col]
    ).properties(
        title=title
    ).configure_title(
        align='center',  
        anchor='middle'  
    )
    return chart

# base player avg chart
def create_avg_rating_chart(df):
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    
    avg_df = df.groupby('Date').agg({'Rating': 'mean'}).reset_index()

    avg_df['Date'] = pd.to_datetime(avg_df['Date'])

    chart = alt.Chart(avg_df).mark_line(point=True).encode(
        x='Date:T',
        y='Rating:Q',
        tooltip=['Date', 'Rating']
    ).properties(
        title="📈 Average Rating",
        width="container"
    )
    return chart
