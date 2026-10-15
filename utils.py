"""
Functions that will be used for all scripts
"""

from itertools import chain, combinations
import spacy
import re


def rm_text_please(original_text, ignore_ls):
    """
    remove a sentence (from ignore_ls) from a string (original_text)

    orginal_text:
        original string

    ignore_ls:
        a list

    output: new_text
    """
    
    # Removes the brackets and everything inside them
    #rm_curling_brackets = re.sub(r'\{.*?\}', '', original_text)
    #result = re.sub(r'\[.*?\]', '', rm_curling_brackets)
    
    # Replace "^" with an empty string
    clean_text = original_text.replace("^", "")

    # Regex Approach: For better performance with many replacements, join the list into a regular expression pattern.
    pattern = "|".join(ignore_ls)
    new_text = re.sub(pattern, "", clean_text, flags=re.IGNORECASE)

    return new_text.strip()


def powerset(s):
    """
    items contains 2 items all then way to all items
    return all combination of a list, range(1, len(s_list) + 1)
    note that range(0, len(s_list) + 1) will include an empty set
    """
    s_list = list(s) # Sets must be converted to lists for indexing
    return list(chain.from_iterable(combinations(s_list, r) for r in range(2, len(s_list) + 1)))


def powerset_4_5(s):
    """
    return n elements from combination of a list
    contains 2 and 3 items
    """
    s_list = list(s) # Sets must be converted to lists for indexing
    # this returns n words combination
    out_list = list(chain.from_iterable(combinations(s_list, r) for r in (range(4, 6))))

    return sorted(out_list)


def powerset_n(s, n):
    """
    return n elements from combination of a list, (range(n,n+1))
    """
    s_list = list(s) # Sets must be converted to lists for indexing
    # this returns n words combination
    out_list = list(chain.from_iterable(combinations(s_list, r) for r in (range(n, n+1))))

    return sorted(out_list)
    

def update_df(df_input):
    """
    Args:
        df_input: input dataframe from a question input file

    Make new column "Topic": concatenate QuestionGroupName and QuestionGroupLabel
        Move covid related sub-level topic to the normal topic.
        For example, change 11601_demographics_(cv19) to 101_demographics
    
    Returns:
        Same dataframes with new columns for topic / cleaned question text
    """
    
    col_keep = ['InstrumentURN', 'InstrumentName', 'QuestionURN', 'QuestionLabel',
       'QuestionItemName', 'QuestionText', 'QuestionGroupID', 'QuestionGroupAgency',
       'QuestionGroupName', 'QuestionGroupLabel']
    df = df_input[col_keep]
    # make sure they are interger
    df['QuestionGroupName'] = df['QuestionGroupName'].astype('Int64')

    # Topic
    df['Topic'] = df['QuestionGroupName'].astype(str) + '_' + df['QuestionGroupLabel'].str.lower().str.replace('|', '').str.replace('/', '_').str.replace(' ', '_')

    df['Topic'] = df['Topic'].replace({'11601_demographics_(cv19)': '101_demographics',
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

    ### TOCHECK ADD 'ADJ','PROPN' ###
    # more than one character, i.e. e-mail contains 'e', '-'
    df['nouns_verbs_lemmas'] = df['QuestionText'].apply(lambda x: set([token.lemma_ for token in nlp(x) if token.pos_ in ['NOUN', 'VERB'] and not token.is_stop and len(token) > 1]))
    df['nouns_verbs_lemmas'] = df['nouns_verbs_lemmas'].apply(lambda x: ['born' if i == 'bear' else i for i in x])

    return df
