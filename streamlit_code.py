# -*- coding: utf-8 -*-
"""Streamlit code.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/abi13-ehub/Podcast_analysis/blob/main/Streamlit%20code.ipynb
"""


from googleapiclient.discovery import build
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import matplotlib.ticker as ticker




api_key = 'AIzaSyDTVR2RoWa9PB3uSVkaptspu4XpdxVM25k'
channel_ids = ['UCzQUP1qoWDoEbmsQxvdjxgQ','UCPxMZIFE856tbTfdkdjzTSQ','UCpeRzRS1b1NvY4og1huE7jw','UC2bBsPXFWZWiBmkRiNlz8vg','UCUOjpYruRCB61RnB846trCQ','UCGX7nGXpz-CmO_Arg-cgJ7A','UCSHZKyawb77ixDdsGog4iWA','UCGq-a57w-aPwyi3pW7XLiHw','UCZjxPbi3AeB6YGKCfQ2TroQ','UCKPxuul6zSLAfKSsm123Vww','UCZxgZTreiWF-12p-GS5R7nQ','UC2D2CMWXMOVWx7giW1n3LIg','UCFo9mvW4ythx_tgT3NHaw-Q','UChMV78lIxhu3eqNtPMJGBtA']
youtube = build('youtube','v3',developerKey = api_key)


def get_channel_stats(youtube,channel_id):

    request = youtube.channels().list(part ='snippet, contentDetails, statistics', id = channel_id)
    response = request.execute()
    data = dict(Channel_name = response['items'][0]['snippet']['title'],
                    Subscribers_count = response['items'][0]['statistics']['subscriberCount'],
                    Total_Views_Count= response['items'][0]['statistics']['viewCount'],
                    Total_Videos= response['items'][0]['statistics']['videoCount'],
                    DateStarted= response['items'][0]['snippet']['publishedAt'],
                    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])
    return data



general_stats = pd.DataFrame()

for i in range(len(channel_ids)):
    data = pd.Series(get_channel_stats(youtube, channel_ids[i])).to_frame().T
    general_stats = pd.concat([general_stats, data], axis=0)

general_stats = general_stats.reset_index(drop=True)


def get_video_ids(youtube, playlist_id):
    request = youtube.playlistItems().list(part = 'contentDetails',playlistId = playlist_id, maxResults=100)
    response = request.execute()
    videos_id = []
    for i in range(len(response['items'])):
        videos_id.append(response['items'][i]['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    more_pages = True

    while more_pages:
        if next_page_token is None:
            more_pages = False
        else:
            request = youtube.playlistItems().list(part = 'contentDetails',playlistId = playlist_id, maxResults=100, pageToken = next_page_token)
            response = request.execute()
            for i in range(len(response['items'])):
                videos_id.append(response['items'][i]['contentDetails']['videoId'])

            next_page_token = response.get('nextPageToken')


    return videos_id


video_ids = []

for i in range(len(channel_ids)):
    video_ids.append(get_video_ids(youtube, general_stats.playlist_id.iloc[i]))


def get_video_details(youtube, video_ids):
    all_video_stats = []
    for i in range(0,len(video_ids),50):
        request = youtube.videos().list(part = 'snippet,statistics',id =','.join(video_ids[i:i+50])) #limit to requests is 50
        response = request.execute()

        for video in response['items']:
            video_stats = dict(Title = video['snippet']['title'], Publish_Date = video['snippet']['publishedAt'],
                                        Views = video['statistics']['viewCount'], Likes = video['statistics'].get('likeCount',0),
                                        Comments = video['statistics'].get('commentCount',0))
            all_video_stats.append(video_stats)
    return all_video_stats



video_dfs = []

for i in range(len(channel_ids)):
    df = pd.DataFrame(get_video_details(youtube, video_ids[i]))
    df['Identity'] = general_stats.Channel_name.iloc[i]  # to know to which channel the video belongs.
    video_dfs.append(df)



video_df = pd.DataFrame()
for df in video_dfs:
    video_df = pd.concat([video_df, df], axis = 0)

video_df = video_df.reset_index(drop= True)


general_stats['Subscribers_count'] = pd.to_numeric(general_stats['Subscribers_count'])
general_stats['Total_Views_Count'] = pd.to_numeric(general_stats['Total_Views_Count'])
general_stats['Total_Videos'] = pd.to_numeric(general_stats['Total_Videos'])
general_stats['DateStarted'] = pd.to_datetime(general_stats['DateStarted'], errors ='coerce').dt.floor('d')



video_df['Publish_Date'] = pd.to_datetime(video_df['Publish_Date']).dt.date.astype('datetime64')
video_df['Views'] = pd.to_numeric(video_df['Views'])
video_df['Likes'] = pd.to_numeric(video_df['Likes'])
video_df['Comments'] = pd.to_numeric(video_df['Comments'])



def top_ten_viewed(df):
    fig, ax = plt.subplots()
    plt.ticklabel_format(style='plain', axis='y')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000000) + 'M'))
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ordered = df.sort_values('Views', ascending=False)
    top_ten = ordered.head(10)
    plt.xticks(rotation=90)
    sns.barplot(y=top_ten['Views'] , x=top_ten['Title'], palette ='Blues_r').set_xticklabels(labels = top_ten['Title']);
    for bar, label in zip(ax.patches, top_ten['Identity']):
        x = bar.get_x()
        width = bar.get_width()
        height = bar.get_height()
        ax.text(x+width/2., height + 0.2, label, ha="center")



def top_ten_viewed_by_name(df, name):
    fig, ax = plt.subplots()
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000000) + 'M'))

    name_df = df[df.Identity == name]
    ordered = name_df.sort_values('Views', ascending=False)
    top_ten = ordered.head(10)
    plt.xticks(rotation=90)
    sns.barplot(y=top_ten['Views'] , x=top_ten['Title'], palette ='Blues_r').set_xticklabels(labels = top_ten['Title']);



def top_ten_Liked(df):
    fig, ax = plt.subplots()
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ordered = df.sort_values('Likes', ascending=False)
    top_ten = ordered.head(10)
    plt.xticks(rotation=90)
    sns.barplot(y=top_ten['Likes'] , x=top_ten['Title'], palette ='Blues_r').set_xticklabels(labels = top_ten['Title']);
    for bar, label in zip(ax.patches, top_ten['Identity']):
        x = bar.get_x()
        width = bar.get_width()
        height = bar.get_height()
        ax.text(x+width/2., height + 0.2, label, ha="center")



def top_ten_Liked_by_name(df, name):
    fig, ax = plt.subplots()
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))
    name_df = df[df.Identity == name]
    ordered = name_df.sort_values('Likes', ascending=False)
    top_ten = ordered.head(10)
    plt.xticks(rotation=90)
    sns.barplot(y=top_ten['Likes'] , x=top_ten['Title'], palette ='Blues_r').set_xticklabels(labels = top_ten['Title']);



def sub_count(df):
    fig, ax = plt.subplots()
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.get_xaxis().set_visible(False)
    names = general_stats['Channel_name']
    subs = general_stats['Subscribers_count']
    names_ordered = general_stats.sort_values('Subscribers_count', ascending=False).Channel_name
    sns.barplot(x=subs, y=names, palette='Blues_r', order=names_ordered).set_yticklabels(labels=names_ordered);
    ax.bar_label(ax.containers[0], fmt = '%d');



def timeline(df):
    fig, ax = plt.subplots();
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    plt.xticks(rotation=90);

    names = general_stats['Channel_name']
    ordered = general_stats.sort_values('DateStarted', ascending=True)

    sns.lineplot(x=ordered['Channel_name'], y=ordered['DateStarted'], palette='Blues', marker="o").set_xticklabels(labels = ordered['Channel_name']);

st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(layout="wide")

sidebar_list = general_stats.Channel_name.tolist()
sidebar_list.insert(0, "General Stats")

side_bar = st.sidebar.selectbox('Which channel would you like to check ?', sidebar_list)

if side_bar == "General Stats":

    st.markdown("<h1 style='text-align: center; color: #8CC0DE;'>YouTube Channel Analysis</h1>", unsafe_allow_html=True)
    st.write("")
    st.write("")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        col1.header("Total Channels")
        col1.write(str(len(general_stats)))

    with col2:
        col2.header("Total Nr. Videos")
        col2.write(str(general_stats.Total_Videos.sum()))

    with col3:
        col3.header("Min Nr. Subs")
        col3.write(str(general_stats.Subscribers_count.min()))

    with col4:
        col4.header("Max Nr. Subs")
        col4.write(str(general_stats.Subscribers_count.max()))


    st.write("")
    st.write("")


    st.write(' #### Subscribers Count ***By Channel*** : ')
    st.pyplot(sub_count(video_df))

    st.write("")

    st.write(' #### ***Timeline*** of Channels creation date : ')
    st.pyplot(timeline(video_df))

    st.write("")

    st.write(' #### Top 10 ***Viewed***  Videos : ')
    st.pyplot(top_ten_viewed(video_df))

    st.write("")

    st.write(' #### Top 10 ***Liked***  Videos : ')
    st.pyplot(top_ten_Liked(video_df))

def st_page(name):

    st.write(f""" # {name} Channel Analysis """)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        col1.header("Subs Count")
        col1.write(str(int(general_stats.Subscribers_count[general_stats.Channel_name == name])))

    with col2:
        col2.header("Total Videos")
        col2.write(str(len(video_df[video_df.Identity == name])))

    with col3:
        col3.header("Total Views")
        col3.write(str(int(general_stats.Total_Views_Count[general_stats.Channel_name == name])))

    with col4:
        col4.header("Date Started")
        col4.write(str(general_stats[general_stats.Channel_name == name]['DateStarted'].astype('datetime64[s]').item().strftime('%Y.%m.%d')))


    st.write("")
    st.write("")

    st.write(' ### Top Ten viewed videos for this channel: ')
    st.pyplot(top_ten_viewed_by_name(video_df, name))

    st.write("")

    st.write(' ### Top 10 liked videos for this channel: ')
    st.pyplot(top_ten_Liked_by_name(video_df, name))

if side_bar == 'PowerfulJRE':
    st_page('PowerfulJRE')

if side_bar == 'BeerBiceps':
    st_page('BeerBiceps')

if side_bar == 'Dostcast':
    st_page('Dostcast')

if side_bar == 'Abhijit Chavda':
    st_page('Abhijit Chavda')

if side_bar == 'Vaad':
    st_page('Vaad')

if side_bar == 'PBD Podcast':
    st_page('PBD Podcast')

if side_bar == 'Lex Fridman':
    st_page('Lex Fridman')

if side_bar == 'The Diary Of A CEO':
    st_page('The Diary Of A CEO')

if side_bar == 'The Jaipur Dialogues':
    st_page('The Jaipur Dialogues')

if side_bar == 'The Cārvāka Podcast':
    st_page('The Cārvāka Podcast')

if side_bar == 'Untriggered with Aminjaz':
    st_page('Untriggered with Aminjaz')

if side_bar == 'Andrew Huberman':
    st_page('Andrew Huberman')

if side_bar == 'Junaid Akram':
    st_page('Junaid Akram')

if side_bar == 'Abhinav Prakash':
    st_page('Abhinav Prakash')

"""<a style='text-decoration:none;line-height:16px;display:flex;color:#5B5B62;padding:10px;justify-content:end;' href='https://deepnote.com?utm_source=created-in-deepnote-cell&projectId=e0375677-767a-4436-b546-4ca5411628af' target="_blank">
<img alt='Created in deepnote.com' style='display:inline;max-height:16px;margin:0px;margin-right:7.5px;' src='data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyB3aWR0aD0iODBweCIgaGVpZ2h0PSI4MHB4IiB2aWV3Qm94PSIwIDAgODAgODAiIHZlcnNpb249IjEuMSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayI+CiAgICA8IS0tIEdlbmVyYXRvcjogU2tldGNoIDU0LjEgKDc2NDkwKSAtIGh0dHBzOi8vc2tldGNoYXBwLmNvbSAtLT4KICAgIDx0aXRsZT5Hcm91cCAzPC90aXRsZT4KICAgIDxkZXNjPkNyZWF0ZWQgd2l0aCBTa2V0Y2guPC9kZXNjPgogICAgPGcgaWQ9IkxhbmRpbmciIHN0cm9rZT0ibm9uZSIgc3Ryb2tlLXdpZHRoPSIxIiBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPgogICAgICAgIDxnIGlkPSJBcnRib2FyZCIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTEyMzUuMDAwMDAwLCAtNzkuMDAwMDAwKSI+CiAgICAgICAgICAgIDxnIGlkPSJHcm91cC0zIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxMjM1LjAwMDAwMCwgNzkuMDAwMDAwKSI+CiAgICAgICAgICAgICAgICA8cG9seWdvbiBpZD0iUGF0aC0yMCIgZmlsbD0iIzAyNjVCNCIgcG9pbnRzPSIyLjM3NjIzNzYyIDgwIDM4LjA0NzY2NjcgODAgNTcuODIxNzgyMiA3My44MDU3NTkyIDU3LjgyMTc4MjIgMzIuNzU5MjczOSAzOS4xNDAyMjc4IDMxLjY4MzE2ODMiPjwvcG9seWdvbj4KICAgICAgICAgICAgICAgIDxwYXRoIGQ9Ik0zNS4wMDc3MTgsODAgQzQyLjkwNjIwMDcsNzYuNDU0OTM1OCA0Ny41NjQ5MTY3LDcxLjU0MjI2NzEgNDguOTgzODY2LDY1LjI2MTk5MzkgQzUxLjExMjI4OTksNTUuODQxNTg0MiA0MS42NzcxNzk1LDQ5LjIxMjIyODQgMjUuNjIzOTg0Niw0OS4yMTIyMjg0IEMyNS40ODQ5Mjg5LDQ5LjEyNjg0NDggMjkuODI2MTI5Niw0My4yODM4MjQ4IDM4LjY0NzU4NjksMzEuNjgzMTY4MyBMNzIuODcxMjg3MSwzMi41NTQ0MjUgTDY1LjI4MDk3Myw2Ny42NzYzNDIxIEw1MS4xMTIyODk5LDc3LjM3NjE0NCBMMzUuMDA3NzE4LDgwIFoiIGlkPSJQYXRoLTIyIiBmaWxsPSIjMDAyODY4Ij48L3BhdGg+CiAgICAgICAgICAgICAgICA8cGF0aCBkPSJNMCwzNy43MzA0NDA1IEwyNy4xMTQ1MzcsMC4yNTcxMTE0MzYgQzYyLjM3MTUxMjMsLTEuOTkwNzE3MDEgODAsMTAuNTAwMzkyNyA4MCwzNy43MzA0NDA1IEM4MCw2NC45NjA0ODgyIDY0Ljc3NjUwMzgsNzkuMDUwMzQxNCAzNC4zMjk1MTEzLDgwIEM0Ny4wNTUzNDg5LDc3LjU2NzA4MDggNTMuNDE4MjY3Nyw3MC4zMTM2MTAzIDUzLjQxODI2NzcsNTguMjM5NTg4NSBDNTMuNDE4MjY3Nyw0MC4xMjg1NTU3IDM2LjMwMzk1NDQsMzcuNzMwNDQwNSAyNS4yMjc0MTcsMzcuNzMwNDQwNSBDMTcuODQzMDU4NiwzNy43MzA0NDA1IDkuNDMzOTE5NjYsMzcuNzMwNDQwNSAwLDM3LjczMDQ0MDUgWiIgaWQ9IlBhdGgtMTkiIGZpbGw9IiMzNzkzRUYiPjwvcGF0aD4KICAgICAgICAgICAgPC9nPgogICAgICAgIDwvZz4KICAgIDwvZz4KPC9zdmc+' > </img>
Created in <span style='font-weight:600;margin-left:4px;'>Deepnote</span></a>
"""
