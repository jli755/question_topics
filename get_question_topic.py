"""
if the combined key words appears in more than one questions then remove these questions
"""

import pandas as pd
import ast
import re
import os
import utils


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
        #df['key_words'] = df['nouns_verbs_lemmas'].apply(lambda x: utils.powerset_4_5( x ))
        df['key_words'] = df['nouns_verbs_lemmas'].apply(lambda x: utils.powerset_n( x, n ))

        # Explode the 'key_words' column
        df_words = df.explode('key_words')
        # Remove rows with NaNs only in specific columns (e.g., 'key_words'):
        df_words.dropna(subset=['key_words'], inplace=True)
        # add a new column to count how many elements in 'key words'
        df_words['num_elements'] = df_words['key_words'].apply(lambda x: len(x) )
        #df_words.to_csv('explode.csv', sep='\t')

        # Add a new column 'word_Count'
        df_words['count_within_topic'] = df_words.groupby(['Topic', 'key_words'])['key_words'].transform('count')
        # sort by topic and count, number of items in key_words desc
        df_words = df_words.sort_values(['Topic', 'count_within_topic', 'num_elements'], ascending=[True, False, False])

        # output key words count only
        df_words_freq = df_words[['Topic', 'key_words', 'count_within_topic']].drop_duplicates(keep='first')

    return df_words_freq


def rm_questions_from_key_words(df, n):
    """Finds a keyword set that matches the most questions, and remove them.

    Args:
        df: a dataframe with a 'QuestionText' column.
        n: The length of keyword sets to try.

    From the QuestionText, extract keywords and build all combinations
    of those keywords, for example with n = 3, this could result in
    ("A", "B", "C"), ("A", "C", "D").
    
    For each keyword set, count the frequency (the number of questions
    that match each set).  For example, ("A", "B", "C") might match 7
    questions and ("A", "C", "D") matches 3.
    
    Next, we remove the questions associated with the most frequent
    keyword set.  In the above, this means we remove the 7 questions
    matching ("A", "B", "C").
    
    Returns:
        Three dataframes.  df after remove questions, summary of what has been removed and removed questions df
    
    """

    df_words_freq = get_freq_key_words(df, n)
    #print(df_words_freq)
    
    if df_words_freq.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    # only remove words if appears in more than one question
    df_words_freq_sub = df_words_freq.loc[df_words_freq['count_within_topic'] >1 ]
    
    if df_words_freq_sub.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    df_summary_before = df.groupby(['Topic']).size().reset_index(name='before_counts')
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

        rm_topic_freq = rm_df.groupby(['Topic']).size().reset_index(name='byTopic')
        
        subset_df = df[df['key_words'].apply(lambda tags_list: words_to_remove not in tags_list)]

        df = subset_df
        #if df.empty:
            # this isn't used when rm_freq_top_n == 1
            #print("Condition met! Stopping loop.")
            #break  # Exits the loop immediately
    #df['removed'] = [list(words_to_remove) for _ in range(len(df))]

    df_summary_after = df.groupby(['Topic']).size().reset_index(name='after_counts')

    if not df_summary_after.empty and not rm_topic_freq.empty:
        df_a = df_summary_after.merge(rm_topic_freq, how = 'left', on = 'Topic')
    else:
        df_a = df_summary_after
    #print(df_a)

    df_summary = pd.merge(df_summary_before, df_a, how = 'left', on='Topic')
    df_summary['words_removed_count'] = [key_words_count_dict] * len(df_summary)
    
    return subset_df, df_summary, rm_df

    
def main():

    # output dir
    os.makedirs('output', exist_ok=True)

    # input
    study = 'NextSteps'
    # study = 'US'     # us 6 items run out of memory
    # study = 'MCS'     # MCS 6 items run out of memory
    # study = 'BCS'
    # study = 'NCDS'
    df_input = pd.read_csv('input_questions/' + study + '_question.csv', sep='\t')
    
    df = utils.update_df(df_input)
    print(df.head(1).transpose())
    
    # Initialize an empty list
    df_count_list = []
    rm_df_list = []
    # loop through Topics
    for t in df['Topic'].unique():
        #print(t)
        df_QG_sub = df[df['Topic'] == t]
        #print(df_QG_sub.head(1).transpose())
        
        for n in [5, 4, 3, 2]:
            #print(n)
            if df_QG_sub.empty:
                break

            #df_QG_sub['key_words'] = df_QG_sub['nouns_verbs_lemmas'].apply(lambda x: utils.powerset_n(x, n))
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
    
    # ast.literal_eval(x)
    final_df_summary['KeyWords'] = final_df_summary['words_removed_count'].apply(lambda x: next(iter(x)))
    final_df_summary['N_questions'] = final_df_summary['byTopic']
    
    # check any duplicated KeyWords?
    # Check for duplicates in the 'name' column (keeping the first)
    duplicates = final_df_summary[final_df_summary['KeyWords'].duplicated(keep='first')]
    #print(duplicates)
    # dict of dict, didn't work because there are duplicates
    # Structure: {col1 -> {col2_name: val2, col3_name: val3}}
    # first column to be the primary key, and the inner dictionary to map the remaining column names to their row values.
    # Set the primary column as the index and export using orient='index'
    #result = final_df_summary[['KeyWords', 'Topic', 'N_questions']].set_index('KeyWords').to_dict(orient='index')
    #result.to_csv(os.path.join('output', 'KeyWord_Topic_' + study + '.tsv'), sep='\t', index=False)
    final_df_summary[['KeyWords', 'Topic', 'N_questions']].to_csv(os.path.join('output', 'KeyWord_Topic_' + study + '.tsv'), sep='\t', index=False)
    
    col_keep = ['InstrumentURN', 'InstrumentName', 'QuestionURN', 'QuestionLabel',
       'QuestionItemName', 'QuestionText', 'QuestionGroupID', 'QuestionGroupAgency',
       'QuestionGroupName', 'QuestionGroupLabel', 'Topic', 
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
    
    rm_df_all_clean[col_keep].to_csv(os.path.join('output', 'removed_all_clean_' + study + '.tsv'), sep='\t', index=False)
        
    # Filter rows where df1's column value is NOT in df2's column
    filtered_df = df[~df['QuestionURN'].isin(rm_df_all_clean['QuestionURN'])]
    filtered_df.to_csv(os.path.join('output', 'not_removed_' + study + '.tsv'), sep='\t', index=False)

if __name__ == "__main__":
    main()

