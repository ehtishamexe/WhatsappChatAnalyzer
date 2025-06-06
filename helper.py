from urlextract import URLExtract
from wordcloud import WordCloud
from collections import Counter
import re
import pandas as pd
import emoji
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

extract = URLExtract()

# -------- Helper functions --------

def fetch_stats(selected_user, df):
    if selected_user == 'overall':
        num_messages = df.shape[0]

        words = []
        for message in df['message']:
            words.extend(message.split())

        num_media_msgs = df[df['message'] == '<Media omitted>\n'].shape[0]

        links = []
        for message in df['message']:
            links.extend(extract.find_urls(message))

        return num_messages, len(words), num_media_msgs, len(links)

    else:
        user_df = df[df['user'] == selected_user]
        num_messages = user_df.shape[0]

        words = []
        for message in user_df['message']:
            words.extend(message.split())

        num_media_msgs = user_df[user_df['message'] == '<Media omitted>\n'].shape[0]

        links = []
        for message in user_df['message']:
            links.extend(extract.find_urls(message))

        return num_messages, len(words), num_media_msgs, len(links)


def most_busy_users(df):
    x = df['user'].value_counts().head()
    df_percent = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
        columns={'index': 'name', 'user': 'percent'}
    )
    return x, df_percent


def create_wordcloud(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    # Drop media messages, deleted messages, and NaN messages
    df = df[~df['message'].isin(['<Media omitted>\n', 'This message was deleted'])]
    df = df.dropna(subset=['message'])  # Remove NaN values from message column

    # Optional: Filter out empty strings if needed
    df = df[df['message'].str.strip() != ""]

    text = df['message'].str.cat(sep=" ")

    wc = WordCloud(width=500, height=500, min_font_size=10, background_color='white')
    df_wc = wc.generate(text)
    return df_wc


def most_common_words(selected_user, df):
    with open('stopenglish.txt', 'r') as f:
        stop_words = set(line.strip() for line in f if line.strip())

    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']

    words = []

    for message in temp['message']:
        for word in message.lower().split():
            word = re.sub(r'\W+', '', word)  # remove punctuation
            if word and word not in stop_words:
                words.append(word)

    if not words:
        return pd.DataFrame(columns=['word', 'count'])

    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    most_common_df.columns = ['word', 'count']
    return most_common_df


def emoji_helper(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    emojis = []
    for message in df['message']:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])

    emoji_df = pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))))
    emoji_df.columns = ['emoji', 'count']
    return emoji_df


# -------- Timeline and Activity functions --------

def monthly_timeline(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    timeline = df.groupby(['year', 'month']).count()['message'].reset_index()

    # Create time label like "Jan-2023"
    timeline['time'] = timeline['month'] + '-' + timeline['year'].astype(str)

    return timeline


def daily_timeline(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    daily_timeline = df.groupby('date').count()['message'].reset_index()
    return daily_timeline


def week_activity_map(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    return df['day_name'].value_counts()


def month_activity_map(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    return df['month'].value_counts()


def activity_heatmap(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    # Assume 'period' is hour or hour range, if missing create it
    if 'period' not in df.columns:
        df['period'] = df['hour'].apply(lambda x: f"{x}:00 - {x}:59")

    user_heatmap = df.pivot_table(index='day_name', columns='period', values='message', aggfunc='count').fillna(0)

    # Reorder days if needed (optional)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    user_heatmap = user_heatmap.reindex(days_order)

    return user_heatmap


# -------- Streamlit Visualization --------

def run_app(df):
    st.title("Whatsapp Chat Analysis")

    selected_user = st.sidebar.selectbox("Select User", options=['overall'] + sorted(df['user'].unique().tolist()))

    # Fetch stats
    num_messages, num_words, num_media, num_links = fetch_stats(selected_user, df)
    st.header(f"Stats for {selected_user}")
    st.write(f"Total Messages: {num_messages}")
    st.write(f"Total Words: {num_words}")
    st.write(f"Media Shared: {num_media}")
    st.write(f"Links Shared: {num_links}")

    # Monthly Timeline
    st.title("Monthly Timeline")
    timeline = monthly_timeline(selected_user, df)
    fig, ax = plt.subplots()
    ax.plot(timeline['time'], timeline['message'], color='green')
    plt.xticks(rotation='vertical')
    st.pyplot(fig)

    # Daily Timeline
    st.title("Daily Timeline")
    daily_tl = daily_timeline(selected_user, df)
    fig, ax = plt.subplots()
    ax.plot(daily_tl['date'], daily_tl['message'], color='black')
    plt.xticks(rotation='vertical')
    st.pyplot(fig)

    # Activity Map
    st.title("Activity Map")
    col1, col2 = st.columns(2)

    with col1:
        st.header("Most Busy Day")
        busy_day = week_activity_map(selected_user, df)
        fig, ax = plt.subplots()
        ax.bar(busy_day.index, busy_day.values, color='purple')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

    with col2:
        st.header("Most Busy Month")
        busy_month = month_activity_map(selected_user, df)
        fig, ax = plt.subplots()
        ax.bar(busy_month.index, busy_month.values, color='orange')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

    # Heatmap
    st.title("Weekly Activity Heatmap")
    user_heatmap = activity_heatmap(selected_user, df)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(user_heatmap, ax=ax)
    st.pyplot(fig)


if __name__ == "__main__":
    # Load your dataframe here, for example:
    # df = pd.read_csv('your_whatsapp_data.csv')

    # For example purpose, assume df is already loaded and has columns:
    # ['date', 'user', 'message', 'year', 'month', 'day', 'day_name', 'hour', 'minute']

    # run_app(df)

    pass
