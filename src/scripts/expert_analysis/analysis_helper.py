import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr
import math


def get_scores_for_beers(rev_with_scores, exp_categories):
    """
    Computes mean, standard deviation, and review count for beers based on specified categories.
    Parameters:
    -----------
    rev_with_scores : pandas.DataFrame
        A DataFrame containing beer reviews with scores. It must include a 'beer_id' column
        and other columns corresponding to expected scoring categories.
    
    exp_categories : list of str
        A list of column names representing the scoring categories (e.g., 'aroma', 'appearance', etc.)
        to include in the aggregation process.

    Returns:
    --------
    scores_for_beer : pandas.DataFrame
        A DataFrame indexed by 'beer_id' containing the following:
            - Mean and standard deviation for each specified category.
            - A 'review_count' column indicating the number of reviews for each beer.
        Only beers with more than one review are included.
    """
    col_to_keep = ['beer_id'] + exp_categories
    scores_for_beer = rev_with_scores.groupby('beer_id').agg(
        {col: ['mean', 'std'] for col in col_to_keep} | {'beer_id': 'count'}
    )

    scores_for_beer = scores_for_beer.rename(columns={'beer_id': 'review_count'})
    scores_for_beer = scores_for_beer[scores_for_beer['review_count']['count']>1]
    return scores_for_beer


def get_min_max_for_beers(rev_with_scores, exp_categories, threshold=1):
    """
    Computes the minimum and maximum scores for beers based on specified categories, 
    with an optional review count filter.

    Parameters:
    -----------
    rev_with_scores : pandas.DataFrame
        A DataFrame containing beer reviews with scores. It must include a 'beer_id' column
        and other columns corresponding to expected scoring categories.

    exp_categories : list of str
        A list of column names representing the scoring categories (e.g., 'aroma', 'appearance', etc.)
        to include in the aggregation process.

    rev_count : bool, optional (default=True)
        If True, includes a 'review_count' column indicating the number of reviews for each beer
        and filters out beers with only one review.

    Returns:
    --------
    scores_for_beer : pandas.DataFrame
        A DataFrame indexed by 'beer_id' containing the following:
            - Minimum and maximum scores for each specified category.
            - If `rev_count` is True, a 'review_count' column indicating the number of reviews for each beer.
        Only beers with more than one review are included when `rev_count` is True.
    """
    col_to_keep = ['beer_id'] + exp_categories
    rev_gruoped = rev_with_scores[col_to_keep].groupby('beer_id')

    scores_for_beer = rev_gruoped.agg(
        {col: ['min', 'max'] for col in col_to_keep} | {'beer_id': 'count'}
    )
    scores_for_beer = scores_for_beer.rename(columns={'beer_id': 'review_count'})
    scores_for_beer = scores_for_beer[scores_for_beer['review_count', 'count']>=threshold]


    return scores_for_beer

def get_min_max_for_style(rev_with_scores, exp_categories):
    col_to_keep = ['style'] + exp_categories
    style_group = rev_with_scores[col_to_keep].groupby('style')

    scores_style = style_group.agg(['min', 'max'])

    return scores_style.reset_index()




def get_mean_scores_beer(rev_with_scores, exp_categories):
    col_to_keep = ['beer_id'] + exp_categories
    mean_scores_beer = rev_with_scores.groupby('beer_id').agg({col: 'mean' for col in col_to_keep} | {'beer_id': 'count'})
    mean_scores_beer =mean_scores_beer.rename(columns={'beer_id': 'review_count'})
    return mean_scores_beer

def get_beer_gr(complete_beer, exp_categories):
    col_to_keep = ['style'] + exp_categories
    return complete_beer[col_to_keep].groupby('style').mean()

def get_users_stats(rev_with_scores, exp_categories, user_id='user_id'):
    col_to_keep = [user_id] + exp_categories
    users = rev_with_scores.groupby(user_id).agg(
        {col: 'mean' for col in col_to_keep} | {user_id: 'count'}
    )

    users = users.rename(columns={user_id: 'nbr_rev'})
    return users

def first_reviews(df,user_id='user_id', max=200):
    """
    Returns the earliest reviews for each user, up to a specified maximum.

    Parameters
    ----------
    df : DataFrame containing user review data, with user_id and 'date' columns.
    max : Maximum number of reviews to return per user (default is 200).

    Returns
    -------
    DataFrame containing up to `max` earliest reviews per user, sorted by user_id and 'date'.
    """

    df = df.sort_values(by=[user_id, 'date'])
    return df.groupby(user_id).head(max)

def joined_date_zero(reviews, user_id='user_id'):
    """
    Normalizes review dates to the first review date for each user, setting their first review as day zero.

    Parameters
    ----------
    reviews : DataFrame containing user review data, with columns user_id and 'date' (assumed to be datetime).

    Returns
    -------
        DataFrame where each user's review dates are adjusted relative to their first review date, 
        so that the first review date for each user is zero.

    Example
    -------
    >>> joined_date_zero(reviews)
    """
    fir_rev = first_reviews(reviews, max=1).rename(columns={'date': 'first_date'})
    reviews = reviews.merge(fir_rev[[user_id, 'first_date']], on=user_id)
    reviews['date'] = reviews['date'] - reviews['first_date'] 
    reviews = reviews.drop(columns=['first_date'])
    return reviews

def standardize_min_max(x, cols, by_style=True,rev_nbr_thr=10, using_min=False):
    """
    Standardizes specified columns in DataFrame `x` based on min and max score for each beer after +1 and logscaling.

    Parameters
    ----------
    x : DataFrame containing data to standardize, with 'beer_id' and columns to be standardized.
    cols : List of column names to standardize in `x`.

    Returns
    -------
        DataFrame `x` with specified columns standardized.
    """
    if by_style:
        max_min_beers = get_min_max_for_style(x, cols)
        merge_on = 'style'
    else:
        max_min_beers = get_min_max_for_beers(x, cols, threshold=rev_nbr_thr).drop(columns=('review_count', 'count')).reset_index()
        merge_on = 'beer_id'
        
    max_min_beers.columns = [merge_on] + [f"{col}_{stat}" for col in cols for stat in ['min', 'max']]

    x = x.merge(max_min_beers, on=merge_on)

    for col in cols:
        min_ = x[f'{col}_min'].apply(lambda val: math.log(val + 1)) if using_min else 0
        max_ = x[f'{col}_max'].apply(lambda val: math.log(val + 1))
        
        x[col] = np.where(min_ == max_, 0, (x[col].apply(lambda val: math.log(val + 1)) - min_) / (max_ - min_))

    x = x.drop(columns=[f"{col}_min" for col in cols] + [f"{col}_max" for col in cols])

    return x

def standardize(x, y, cols):
    """
    Standardizes specified columns in DataFrame `x` based on means and standard deviations in DataFrame `y`.

    Parameters
    ----------
    x : DataFrame containing data to standardize, with 'beer_id' and columns to be standardized.
    y : DataFrame with 'beer_id' and statistical information for standardization, including means and standard deviations.
    cols : List of column names to standardize in `x`.

    Returns
    -------
        DataFrame `x` with specified columns standardized.
    """
    y_copy = y.drop(columns=['review_count'])
    y_copy.columns = ['beer_id'] + [f"{col}_{stat}" for col in cols for stat in ['mean', 'std']]

    x = x.merge(y_copy, on='beer_id')

    for col in cols:
        std = x[f"{col}_std"]
        x[col] = np.where(std != 0, (x[col] - x[f"{col}_mean"]) / std, x[col] - x[f"{col}_mean"])

    x = x.drop(columns=[f"{col}_mean" for col in cols] + [f"{col}_std" for col in cols])

    return x

def review_of_experts(df, users, user_id='user_id', nbr_rev=100):
    x = df.merge(users[[user_id,'nbr_reviews']], on=user_id)
    return x[x['nbr_reviews']>nbr_rev]

def corr_and_count(group, att_1='expertness_score', replace_date=False):
    """
    Calculates the correlation between att_1 and 'date' within a given group, 
    along with the count of 'date' entries.

    Parameters
    ----------
    group :  A DataFrame group with columns att_1 and 'date'.
    att_1 : name of the first column
    replace_date : bool if True replace the date with an incremental counter

    Returns
    -------
    A Series containing:
        - 'correlation': The correlation between att_1 and 'date'. If the standard deviation 
          of either column is zero, the correlation is set to NaN.
        - 'total_count': The count of non-NaN entries in the 'date' column.

    """
    if(replace_date):
        group = group.sort_values(by='date')
        group['date'] = range(len(group))
        
    count = group['date'].count()
    if group[att_1].std() == 0 or group['date'].std() == 0 or len(group['date'])<2:
        correlation= float('nan') 
        p_value = float('nan')
    else:
        correlation, p_value = pearsonr(group[att_1], group['date'].astype(int))
    
    return pd.Series({'correlation': correlation,'p_value': p_value,  'total_count': count})

def plot_corr_and_pvalue(result):
    fig, axes = plt.subplots(1, 4, figsize=(12, 6), sharey = True) 


    fig.suptitle("Correlation and p-values by Review Count", fontsize=16)
    sns.boxplot(y=result['correlation'], ax=axes[0])
    axes[0].set_title("Correlation (All Data)")
    axes[0].set_ylabel("Correlation / p-value")

    sns.boxplot(y=result[result['total_count'] > 200]['correlation'], ax=axes[1])
    axes[1].set_title("Correlation (Reviews > 200)")

    sns.boxplot(y=result['p_value'], ax=axes[2])
    axes[2].set_title("P-value (All Data)")

    sns.boxplot(y=result[result['total_count'] > 200]['p_value'], ax=axes[3])
    axes[3].set_title("P-value (Reviews > 200)")

    plt.tight_layout()  
    plt.show()