"""
if the combined key words appears in more than one questions then remove these questions
"""

from itertools import chain, combinations
import pandas as pd
import spacy
import ast
import re
import os


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
    result = re.sub(r'\{.*?\}', '', original_text)

    # Regex Approach: For better performance with many replacements, join the list into a regular expression pattern.
    pattern = "|".join(ignore_ls)
    new_text = re.sub(pattern, "", result, flags=re.IGNORECASE)
    return new_text


def words_to_lemma(in_text, nlp):
    """
    returns the base dictionary form (lemma) of a word
    """
    # Remove outer brackets
    word_list = re.findall(r'"\s*([^"]*?)\s*"', in_text)

    # Join the list into a string and process it with spaCy
    text = " ".join(word_list)
    doc = nlp(text)

    # Extract the lemma for each token
    lemmas = [token.lemma_ for token in doc]
    lemmas = ['born' if i == 'bear' else i for i in lemmas]

    return lemmas


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


def get_freq_key_words(df, n):
    """
    df_not_assigned has a column called nouns_verbs_lemmas
    permute and count, modifies the input df
    calculate frequency of all combinations of key words
    """
    if df.empty:
        df_words_freq = pd.DataFrame()
    else:
        # Convert the string back into a real Python list object
        #df['key_words'] = df['nouns_verbs_lemmas'].apply(lambda x: powerset_4_5( x ))
        df['key_words'] = df['nouns_verbs_lemmas'].apply(lambda x: powerset_n( x, n ))

        # Explode the 'key_words' column
        df_words = df.explode('key_words')
        # Remove rows with NaNs only in specific columns (e.g., 'key_words'):
        df_words.dropna(subset=['key_words'], inplace=True)
        # add a new column to count how many elements in 'key words'
        df_words['num_elements'] = df_words['key_words'].apply(lambda x: len(x) )
        #df_words.to_csv('explode.csv', sep='\t')

        # Add a new column 'word_Count'
        df_words['count_within_topic'] = df_words.groupby(['topic', 'key_words'])['key_words'].transform('count')
        # sort by topic and count, number of items in key_words desc
        df_words = df_words.sort_values(['topic', 'count_within_topic', 'num_elements'], ascending=[True, False, False])

        # output key words count only
        df_words_freq = df_words[['topic', 'key_words', 'count_within_topic']].drop_duplicates(keep='first')

    return df_words_freq


def rm_questions_from_key_words(df, n):
    """
    given a dataframe of one topic with question text df['QuestionText']
    find all combinations of key words
    count frequency within the df
     - number of elements of key words combination is more than 3
    remove questions associated with the most freq comb
    out put both new dataframe and the (key words), also number of questions removed
    """

    df_words_freq = get_freq_key_words(df, n)
    #print(df_words_freq)
    
    if df_words_freq.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    # only remove words if appears in more than one question
    df_words_freq_sub = df_words_freq.loc[df_words_freq['count_within_topic'] >1 ]
    
    if df_words_freq_sub.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    df_summary_before = df.groupby(['topic']).size().reset_index(name='before_counts')
    # print(df_summary_before)

    # remove questions, normally we would remove one words_to_remove for each outer iteration
    # but in theory this code supports removing multiple words_to_remove per iteration
    rm_freq_top_n = 1
    df_words_freq_n = df_words_freq_sub.head(rm_freq_top_n)
    key_words_count_dict = dict(zip(df_words_freq_n['key_words'], df_words_freq_n['count_within_topic']))

    groups_of_words_to_remove = df_words_freq_n['key_words'].to_list()
    #print("** " * 30)
    #print(groups_of_words_to_remove )
    rm_topic_freq = pd.DataFrame()
    subset_df = pd.DataFrame()
    for words_to_remove in groups_of_words_to_remove:
        #print(f"words_to_remove={words_to_remove}")
          
        rm_df = df[df['key_words'].apply(lambda tags_list: words_to_remove in tags_list)]
        #print(rm_df.head(1).transpose())
        if not rm_df.empty:
            rm_df['removed_words'] = rm_df.apply(lambda _: words_to_remove, axis=1)

        rm_topic_freq = rm_df.groupby(['topic']).size().reset_index(name='byTopic')
        
        subset_df = df[df['key_words'].apply(lambda tags_list: words_to_remove not in tags_list)]

        df = subset_df
        #if df.empty:
            # this isn't used when rm_freq_top_n == 1
            #print("Condition met! Stopping loop.")
            #break  # Exits the loop immediately
    #df['removed'] = [list(words_to_remove) for _ in range(len(df))]

    df_summary_after = df.groupby(['topic']).size().reset_index(name='after_counts')

    if not df_summary_after.empty and not rm_topic_freq.empty:
        df_a = df_summary_after.merge(rm_topic_freq, how = 'left', on = 'topic')
    else:
        df_a = df_summary_after
    #print(df_a)

    df_summary = pd.merge(df_summary_before, df_a, how = 'left', on='topic')
    df_summary['words_removed_count'] = [key_words_count_dict] * len(df_summary)
    
    return subset_df, df_summary, rm_df

    
def main():

    # output dir
    os.makedirs('output', exist_ok=True)

    # input
    #study = 'NextSteps'
    #study = 'US'
    study = 'MCS'
    df_input = pd.read_csv('input_questions/' + study + '_question.csv', sep='\t')
    col_keep = ['InstrumentURN', 'InstrumentName', 'QuestionURN', 'QuestionLabel',
       'QuestionItemName', 'QuestionText', 'QuestionGroupID', 'QuestionGroupAgency',
       'QuestionGroupName', 'QuestionGroupLabel']
    df = df_input[col_keep]
    # make sure they are interger
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

    ### TOCHECK ADD 'ADJ','PROPN' ###
    df['nouns_verbs_lemmas'] = df['QuestionText'].apply(lambda x: set([token.lemma_ for token in nlp(x) if token.pos_ in ['NOUN', 'VERB'] and not token.is_stop]))
    df['nouns_verbs_lemmas'] = df['nouns_verbs_lemmas'].apply(lambda x: ['born' if i == 'bear' else i for i in x])

    # print(df.head(1).transpose())
    #df_subset = df.loc[df['topic'] == '10201_housing']
    #df_sub = df[sub_columns]
    df_sub = df
    #print(df_subset.head(1).transpose())
    
    # Initialize an empty list
    df_count_list = []
    rm_df_list = []
    # loop through topics
    for t in df_sub['topic'].unique():
        #print(t)
        df_QG_sub = df_sub[df_sub['topic'] == t]
        #print(df_QG_sub.head(1).transpose())
        
        for n in [5, 4, 3, 2]:
            #print(n)
            if df_QG_sub.empty:
                break

            #df_QG_sub['key_words'] = df_QG_sub['nouns_verbs_lemmas'].apply(lambda x: powerset_n(x, n))
            #print(df_QG_sub.head(1).transpose())
        
            ## TODO: do until rm_questions_from_key_words returns empty df   
        
            # remove twice, recalculating freq between each removal
            df_summary_step_list = []
            rm_df_step_list = []
            i = 1
            while True:
                #print(df_QG_sub.size)
                print(i)
                df_new, df_summary_new, rm_df = rm_questions_from_key_words(df_QG_sub, n)

                if df_new.empty and df_summary_new.empty and rm_df.empty:
                     break
                df_summary_new['step_n'] = i
                df_summary_step_list.append(df_summary_new)
                rm_df_step_list.append(rm_df)
                df_QG_sub = df_new
                i = i + 1
                #print(f"i={i}: {len(df_QG_sub)}")
                #print(df_summary_step_list)
                
            if not df_summary_step_list == []:
                df_summary_step = pd.concat(df_summary_step_list, ignore_index=True)
                rm_df_step = pd.concat(rm_df_step_list, ignore_index=True)

                df_count_list.append(df_summary_step)
                rm_df_list.append(rm_df_step)

                # df_summary_step.to_csv(os.path.join('output', 'count_summary_' + str(t) + '.tsv'), sep='\t', index=False)

    # Concatenate all DataFrames in the list at once
    final_df_summary = pd.concat(df_count_list, ignore_index=True)
    # remove before_counts=0 row
    final_df_summary.dropna(subset=['before_counts'], inplace=True)
    # Fill column with 0 and update the DataFrame
    final_df_summary['after_counts'] = final_df_summary['after_counts'].fillna(0)
    # output
    final_df_summary.to_csv(os.path.join('output', 'key_words_summary_' + study + '.tsv'), sep='\t', index=False)
    
    # output keyword-topic pair 
    #by_study_dir = 'output/KeyWords_Topic_by_study'
    # ast.literal_eval(x)
    final_df_summary['KeyWords'] = final_df_summary['words_removed_count'].apply(lambda x: next(iter(x)))
    final_df_summary[['KeyWords', 'topic']].to_csv(os.path.join('output', 'KeyWords_Topic_' + study + '.tsv'), sep='\t', index=False)
    
    col_keep = ['InstrumentURN', 'InstrumentName', 'QuestionURN', 'QuestionLabel',
       'QuestionItemName', 'QuestionText', 'QuestionGroupID', 'QuestionGroupAgency',
       'QuestionGroupName', 'QuestionGroupLabel', 'topic', 
       'QuestionTextOriginal', 'nouns_verbs_lemmas', 
       'removed_words']
  
    rm_df_all = pd.concat(rm_df_list, ignore_index=True)
    #print(rm_df_all.head(1).transpose())
    # Convert the list column to tuples
    rm_df_all['nouns_verbs_lemmas'] = rm_df_all['nouns_verbs_lemmas'].apply(tuple)
    rm_df_all['key_words'] = rm_df_all['key_words'].apply(tuple)
    rm_df_all['removed_words'] = rm_df_all['removed_words'].apply(tuple)
    # Remove duplicate rows across all columns
    rm_df_all_clean = rm_df_all.drop_duplicates()
    
    rm_df_all_clean[col_keep].to_csv(os.path.join('output', 'removed_all_clean.tsv'), sep='\t', index=False)
        
    # Filter rows where df1's column value is NOT in df2's column
    filtered_df = df[~df['QuestionURN'].isin(rm_df_all_clean['QuestionURN'])]
    filtered_df.to_csv(os.path.join('output', 'not_removed.tsv'), sep='\t', index=False)

if __name__ == "__main__":
    main()

