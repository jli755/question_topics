Topics from Question Text
=========================

Workflow
--------

Given a collection of existing questions with associated topics for a study.

Filter out some words.  Extract keyword/topic pairs.  Choose the most frequently occuring keywords within a topic.  Remove questions associated with that chosen keyword set.  Repeat.

Output should be keyword/topic pairs that can then be used to assign topics to new questions.


File structure
--------------

- folder `input_questions/`
    - NextStep
    - MCS
- folder `resources/`
    - Ignore_Sentences, use this to remove part of the qustion text
    - KeyWord_Topic, use this to assign topic to a question based on it's key words
  
- script: `assign_topic.py`

- script: `get_question_topic.py`
    - output 
         - key words and topics summary
         - questions that are removed and not removed files
