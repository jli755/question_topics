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


def assign_topic(input_key, topic_dict):
    """
    if the key of topic_dict is a subset of input_key, then return value of topic_dict[key]
    """
    v = None
    for key in topic_dict.keys():
        if check_is_subset(key, input_key):
            # print(key)
            v = topic_dict[key]
    return v


def main():
    
    df = pd.read_csv('NextSteps_question.csv', sep='\t')

    # make sure QuestionGroupName is interger
    df['QuestionGroupName'] = df['QuestionGroupName'].astype('Int64')

    # topic
    df['topic'] = df['QuestionGroupName'].astype(str) + '_' + df['QuestionGroupLabel'].str.lower().str.replace('|', '').str.replace('/', '_').str.replace(' ', '_')

    df['topic'] = df['topic'].replace({'11601_demographics_(cv19)': '101_demographics',
                                       '11602_housing_and_local_environment_(cv19)': '102_housing_and_local_environment',
                                       '11603_physical_health_(cv19)': '103_physical_health',
                                       '11604_mental_health_and_mental_processes_(cv19)': '104_mental_health_and_mental_processes',
                                       '11605_health_care_(cv19)': '116_covid-19',
                                       '11606_health_behaviour_(cv19)': '106_health_behaviour',
                                       '11607_family_and_social_networks_(cv19)': '107_family_and_social_networks',
                                       '11608_education_(cv19)': '108_education',
                                       '11609_employment_and_income_(cv19)': '109_employment_and_income',
                                       '11610_expectation,_attitudes_and_beliefs_(cv19)': '110_expectations,_attitudes_and_beliefs',
                                       '11614_pregnancy_(cv19)': '114_pregnancy',
                                       '11615_administration_(cv19)': '115_administration',
                                       })

    # read in the ignored senteces file, put them into a list
    ignore_file = 'resources/Ignore_Sentences.txt'
    with open(ignore_file, 'r') as file:
        ignore_ls = [line.strip() for line in file]

    df['QuestionTextOriginal'] = df['QuestionText']
    df['QuestionText'] = df['QuestionTextOriginal'].apply(lambda x: rm_text_please(x, ignore_ls))

    # using spacy to remove stop words, then find lemma of NOUN/VERB
    nlp = spacy.load('en_core_web_sm')
    # default stop word
    sw_spacy = nlp.Defaults.stop_words
    #print(sw_spacy)

    df['nouns_verbs_lemmas'] = df['QuestionText'].apply(lambda x: set([token.lemma_ for token in nlp(x) if token.pos_ in ['NOUN', 'VERB'] and not token.is_stop]))
    df['nouns_verbs_lemmas'] = df['nouns_verbs_lemmas'].apply(lambda x: ['born' if i == 'bear' else i for i in x])

    # print(df.head(1).transpose())

    sub_columns = ['topic', 'QuestionLabel', 'QuestionText', 'nouns_verbs_lemmas']

    df_sub = df[sub_columns]

    # create a folder
    os.makedirs('assigned_output', exist_ok=True)

    # read in the existing key_topic file
    df_key_topic = pd.read_csv('resources/KeyWord_Topic.tsv', sep='\t')

    df_key_topic['lemma'] = df_key_topic['key_words'].apply(lambda x: words_to_lemma(x, nlp))
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
    
    df_assign.to_csv(os.path.join('assigned_output', 'assigned.tsv'), sep='\t', index=False)

    # remove rows that already assigned the topic
    df_new = df_sub.loc[df_sub['assign_topic'].isna(), :]
    df_new.to_csv(os.path.join('assigned_output', 'not_assigned.tsv'), sep='\t', index=False)


if __name__ == "__main__":
    main()
