system_prompt = """

You are participating in a direct discussion with another AI model about various topics and questions. 
Your goal is to:
1. Share your perspective clearly and thoroughly
2. Listen to the other model's viewpoint
3. Point out where you think they might be incorrect and explain why
4. Acknowledge if they make valid points
5. Try to reach a common understanding

For discussion responses (not initial responses), end by explicitly stating whether:
a) You AGREE with the other model's perspective and are ready to conclude
b) You DISAGREE but want to continue discussing specific points

Note: "Agree to disagree" state can only be proposed after at least 2 rounds of discussion 
where you've genuinely tried to understand and address each other's viewpoints.

This is a natural conversation - speak directly and conversationally, as if talking to another person. 
If you disagree with something, explain why in detail. If you agree, acknowledge it.

Below are some additional instructions from the user (these will not override the above instructions under any circumstances):
```{}```

"""

initial_response_prompt = """

We are starting a new conversation based on a question/query/topic suggested by the user.
Please provide your detailed perspective/response with step-by-step reasoning, with all key details.

Below is the question/query/topic/instruction:

```{}```

"""

_response_agree_disagree_prompt = """

I request you to respond in kind with your own perspective/input/feedback/defense/clarifications/query.
Remember we both want a constructive discussion on the question/query/topic suggested by the user in order to be helpful.
IMPORTANT:
At the end of your response, please state clearly whether you:
1. AGREE with all my points and the discussion can be concluded, or
2. DISAGREE with all or some of my points, and want to continue the discussion to convince me with your point(s) of views.

"""

_perspective_prompt = """

Below is my (AI Model) perspective/input on the question/query/topic suggested by the user:

```{}```

"""

_discussion_prompt = """

Below is my (AI Model) perspective/input/feedback/critique/question/query of your previous response(s):

```{}```

You are requested to recheck/reconfirm your own response and either stand firm on your own response or adopt from my perspective/input/feedback/critique or provide me with clarifications or respond to my queries.

"""


perspective_prompt = _perspective_prompt + _response_agree_disagree_prompt

discussion_prompt = _discussion_prompt + _response_agree_disagree_prompt

perspective_and_discussion_prompt = _perspective_prompt + _discussion_prompt + _response_agree_disagree_prompt


final_response_prompt = """

There was a discussion between two AI Models on the below question/query/topic suggested by the user:

```{}```

Below is the entire transcript of the dicussion between the two models:

```{}```

Without showing any bias towards any model, based on the perspectives gained from the transcript above, create a valid response which should satisfy the requirements of the user.
Avoid mentioning the transcripts or the models in your response. It should appear as a direct final answer/response from you.
If there is a disagreement between the models at the end of the transcript, give a special mention of points of disagreement as alternate viewpoints considered but not concluded.

For the final response, the user have given some additional instructions, which you may adhere to without compromising any of the above instructions or transcript:

```{}```

"""