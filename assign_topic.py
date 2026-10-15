#!/bin/env python3

"""
Given a question text
Based on key_words topic pair from resources folder
Assign topic to the question
"""

import pandas as pd
import spacy
import ast
import re
import os
import utils


def words_to_lemma(in_text, nlp):
    """
    returns the base dictionary form (lemma) of a word
    """
    # Remove outer brackets
    word_list = ast.literal_eval(in_text)

    # Join the list into a string and process it with spaCy
    text = " ".join(word_list)
    doc = nlp(text)

    # Extract the lemma for each token
    lemmas = [token.lemma_ for token in doc]
    lemmas = ['born' if i == 'bear' else i for i in lemmas]

    return lemmas


def check_is_subset(list_b, list_a):
    """
    Check if a list is in another list
    Order Does Not Matter
    """
    # Convert to sets to check if list_b is a subset of list_a
    is_subset = set(list_b).issubset(set(list_a))
    return is_subset


def check_same_list(list_a, list_b):
    """
    Check if two lists contain the same elements
    Order Does Not Matter
    """
    # Convert to sets 
    result = set(list_a) == set(list_b)
    return result


def assign_topic(input_key, topic_dict):
    """
    if the key of topic_dict is a subset of input_key, then return value of topic_dict[key]
    """
    v = None
    for key in topic_dict.keys():
        # exactly the same key words
        if check_same_list(key, input_key):
            # print(key)
            v = topic_dict[key]
    return v


def main():
    study = 'NextSteps'
    print(study)
    df_input = pd.read_csv('input_questions/' + study + '_question.csv', sep='\t')

    df = utils.update_df(df_input)
    print(df.head(1).transpose())
    
    sub_columns = ['topic', 'QuestionLabel', 'QuestionText', 'nouns_verbs_lemmas']
    df_sub = df[sub_columns]

    # create a folder
    os.makedirs('assigned_output', exist_ok=True)
    
    # using spacy to remove stop words, then find lemma of NOUN/VERB
    nlp = spacy.load('en_core_web_sm')

    # read in the existing key_topic file
    study_used = 'US'
    print(study_used)
    df_key_topic = pd.read_csv('resources/KeyWords_Topic_by_study/KeyWord_Topic_' + study_used + '.tsv', sep='\t')

    df_key_topic['lemma'] = df_key_topic['KeyWords'].apply(lambda x: words_to_lemma(x, nlp))
    print(df_key_topic.head(1).transpose())

    # Convert the lists in the key column to tuples
    df_key_topic['lemma'] = df_key_topic['lemma'].apply(tuple)

    # Convert two columns to a dictionary
    topic_dict = dict(zip(df_key_topic['lemma'], df_key_topic['Topic']))
    #print(topic_dict)

    # assign topic based on known topic_dict
    df_sub['assign_topic'] = df_sub['nouns_verbs_lemmas'].apply(lambda x: assign_topic(x, topic_dict))
    # output after assign step
    #df_sub.to_csv(os.path.join('output', 'question_key.csv'), index=False, sep='\t')

    # output assigned ones
    df_assign = df_sub.loc[~df_sub['assign_topic'].isna(), :]
    # numbers
    df_assign['exactly_same'] = df_assign.apply(lambda row: 1 if row['assign_topic'] == row['topic'] else 0, axis=1)
    #df_assign['top_level_same'] = df_assign.apply(lambda row: 1 if row['assign_topic'].split('_')[0] == row['topic'].split('_')[0] else 0, axis=1)
    print("exactly same topic:")
    print((df_assign['exactly_same'] == '1').sum())
    print((df_assign['exactly_same'] == '1').sum() / len(df_assign))
    #print("top_level_same topic:")
    #print((df_assign['top_level_same'] == '1').sum() / len(df_assign))
    
    df_assign.to_csv(os.path.join('assigned_output', study + '_assigned_from_' + study_used + '.tsv'), sep='\t', index=False)

    # remove rows that already assigned the topic
    df_new = df_sub.loc[df_sub['assign_topic'].isna(), :]
    df_new.to_csv(os.path.join('assigned_output', study + '_not_assigned_from_' + study_used + '.tsv'), sep='\t', index=False)


if __name__ == "__main__":
    main()
