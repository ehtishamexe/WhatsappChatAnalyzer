import re
import pandas as pd

def preprocess(data):
    # Pattern to split messages and extract dates
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[APMapm]{2}\s-\s'
    
    # Split messages and get dates
    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)
    
    # Create DataFrame
    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    
    # After creating the df with 'message_date' column extracted via regex
    df['message_date'] = df['message_date'].str.replace(r'\s-\s$', '', regex=True)
    df['message_date'] = pd.to_datetime(df['message_date'], format='%m/%d/%y, %I:%M %p', errors='coerce')

    
    # Rename column
    df.rename(columns={'message_date': 'date'}, inplace=True)
    
    users = []
    messages = []
    
    # Extract user and message content
    for message in df['user_message']:
        entry = re.split(r'([\w\W]+?):\s', message, maxsplit=1)
        if len(entry) > 2:  # user name exists
            users.append(entry[1])
            messages.append(entry[2])
        else:
            users.append('group_notification')
            messages.append(entry[0])
    
    df['user'] = users
    df['message'] = messages
    
    # Drop the original user_message column
    df.drop(columns=['user_message'], inplace=True)
    
    # Extract datetime features
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute
    
    # Drop unwanted columns
    df.drop(['only_date', 'month_num'], axis=1, inplace=True)
    
    return df
