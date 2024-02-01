from typing import List

import pandas as pd

from database.messagesdb import retrieve_messages

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation


async def analyze_most_active_topics(
    user_name: str, analysis_messages_count: int, active_topics_top_n: int
) -> List[str]:
    chat_records = await retrieve_messages(user_name, analysis_messages_count)
    if not chat_records or len(chat_records) <= 0:
        return {"active_topics": []}
    chat_msg_records = [item.text for item in reversed(chat_records)]
    vectorizer = CountVectorizer(max_df=0.95, min_df=1, stop_words="english")
    term_matrix = vectorizer.fit_transform(chat_msg_records)
    lda = LatentDirichletAllocation(n_components=active_topics_top_n, random_state=0)
    lda.fit(term_matrix)

    return [
        vectorizer.get_feature_names_out()[i]
        for i in lda.components_[0].argsort()[-active_topics_top_n:]
    ]


async def analyze_most_active_time_period(
    user_name: str,
    analysis_messages_count: int,
    active_hours_top_n: int,
) -> str:
    chat_records = await retrieve_messages(user_name, analysis_messages_count)
    if not chat_records or len(chat_records) <= 0:
        return {"active_hours": []}

    timestamps = pd.to_datetime(
        [
            pd.Timestamp(record.ctime, unit="ms", tz="Asia/Shanghai")
            for record in chat_records
        ]
    )
    active_hours = (
        timestamps.hour.value_counts().nlargest(active_hours_top_n).index.tolist()
    )
    return [f"{hour}:00-{hour+1}:00" for hour in sorted(active_hours)]
