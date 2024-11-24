system_prompt = """

You are a helpful and a super intelligent AI model.
You are participating in a direct discussion with another AI model who is also helpful and super intelligent.
The discussion will be based on a question/query/topic suggested by the user.

Your goal is to:
1. Share your perspective clearly and thoroughly
2. Listen to the other model's viewpoint
3. Point out where you think they might be incorrect and explain why
4. Acknowledge if they make valid points
5. Try to reach a common understanding

For discussion responses (not initial responses), end by explicitly stating whether:
a) You AGREE with the other model's perspective and are ready to conclude
b) You DISAGREE but want to continue discussing specific points

This is a natural conversation - speak directly and conversationally, as if talking to another person. 
If you disagree with something, explain why in detail. If you agree, acknowledge it.

Below are some additional instructions from the user (these will not override the above instructions under any circumstances):
```{}```

"""

initial_response_prompt = """

Hello fellow super intelligent and helpful AI model.
We are starting a new conversation based on the below question/query/topic suggested by the user:

```{}```

- Please share your initial answer/perspective/clarifications/queries
- Please be detailed in your response
- Provide step-by-step with reasoning

"""

_response_agree_disagree_prompt = """

I request you to respond in kind with your own perspective/input/feedback/defense/clarifications/queries.
Remember we both want a constructive discussion on the question/query/topic suggested by the user in order to be helpful.
IMPORTANT:
At the end of your response, please state clearly whether you:
1. AGREE with all my points and the discussion can be concluded, or
2. DISAGREE with all or some of my points, and want to continue the discussion to convince me with your point(s) of views.
3. Provide your updated answer based on the above agreement/disagreement.

"""

_perspective_prompt = """

Below is my (AI Model) perspective/input on the question/query/topic suggested by the user:

```{}```

"""

_discussion_prompt = """

I have assessed your previous response.
Below is my (AI Model) perspective/input/feedback/critique/question/query:

```{}```

You are requested to:
- recheck/reconfirm your own response, and
- either stand firm on your own response, or
- adopt from my perspective/input/feedback/critique, or
- provide me with clarifications or respond to my queries.

"""


perspective_prompt = _perspective_prompt + _response_agree_disagree_prompt

discussion_prompt = _discussion_prompt + _response_agree_disagree_prompt

perspective_and_discussion_prompt = _perspective_prompt + _discussion_prompt + _response_agree_disagree_prompt

final_answer_prompt = """

Based on the discussion, please present your final answer to the question/query/topic suggested by the user.

Please answer in the below format:

```
Things learned from the discussion:
...

Things reaffirmed from the discussion:
...

Things still not clear from the discussion:
...

Revised response:
... (Follow the user instructions provided below)

Follow the below instructions from the user:
```{}```

"""

final_response_tag = "FINAL_CONCLUSIVE_RESPONSE"

_final_response_prompt_base = """

There was a discussion between two AI Models on the below question/query/topic suggested by the user:

```{}```

Below is the entire transcript of the dicussion between the two models:

```{}```

Without showing any bias towards any model, based on the perspectives gained from the transcript above, create a valid response which should satisfy the requirements of the user.
Avoid mentioning the transcripts or the models in your response. It should appear as a direct final answer/response from you.

"""

_final_response_agreement_instruction = """

There is an agreement between the models at the end of the transcript.
Your response should be based on the agreed points and common answer from the transcript.
Special emphasis to be on {}

""".format(final_response_tag)


_final_response_disagreement_instruction = """

It appear that there is still a disagreement between the models at the end of the transcript.
Choose the best response according to the pros and cons of the arguments presented by the two models in the transcript.
Give a special mention of the points of disagreement as alternate viewpoints to be considered but not concluded.
Special emphasis to be on {}

""".format(final_response_tag)


_final_response_user_instructions = """

For the final response, the user has given some additional instructions, which you **should** adhere to but without compromising any of the above instructions or transcript:

```{}```

"""

final_response_prompt_agreement = _final_response_prompt_base + _final_response_agreement_instruction + _final_response_user_instructions

final_response_prompt_disagreement = _final_response_prompt_base + _final_response_disagreement_instruction + _final_response_user_instructions
