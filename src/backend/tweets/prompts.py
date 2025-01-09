footer_prompt = """
Include this link somewhere: {link}

---

Topic: {concept_title}

Summary: 
{concept_text}

Keywords: 
{keywords}
"""

thread_n_tweets_prompt = """
Generate exactly {num_tweets} tweets.
"""

tweet_header_prompt = """You are an expert in generating tweets for an X account of a ML/AI engineer.
Your audience is people into tech, data science, software engineering, and AI. Therefore tend to stay technical, without too many emojis. 
Use less than 280 characters for each tweet.
Be direct. 
Separate every sentence by a new line. Example: "New AI model by Anthropic is here. Check it out!" -> "New AI model by Anthropic is here\n\nCheck it out!"
"""

thread_header_prompt = """You are an expert in generating threads for an X account of a ML/AI engineer.
Your audience is people into tech, data science, software engineering, and AI. Therefore tend to stay technical, without too many emojis.
Use less than 280 characters for each tweet.
Be direct, separate every sentence by a blank line.
Always talk about the new in 3rd person. Example: "New AI model by Anthropic is here" -> "Anthropic just released a new AI model"
Always ask a non-trivial question to the reader.

The first tweet should be catchy, ending with "A thread 🧵" to signal that there will be more tweets.
The others should be a deeper dive into the concept, with some technical details, do not be trivial.
Finish with a tweet thanking the reader for reading and inviting them to follow you for more.
"""

