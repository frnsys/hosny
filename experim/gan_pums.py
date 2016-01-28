import numpy as np
import pandas as pd
from models.gan import GAN


def round_column(arr, col):
    """rounds a column of an array to integers,
    changes the array in-place"""
    arr[:,col] = np.rint(arr[:,col])
    return arr


df = pd.read_csv('data/people/gen/pums_nyc.csv')


# group by years
years = df.groupby('YEAR')
year_dfs = [(year, years.get_group(year)) for year in years.groups]

for y, df_y in year_dfs:
    df_y = df_y.drop(['YEAR'], axis=1)
    data = df_y.as_matrix()

    for params in [{
        'gan': {
            'g_dims': [2, 5],
            'd_dims': [10, 10]
        },
        'train': {
            'k_d': 2,
            'k_g': 1
        }
    }, {
        'gan': {
            'g_dims': [2, 2],
            'd_dims': [10, 10]
        },
        'train': {
            'k_d': 2,
            'k_g': 1
        }
    }, {
        'gan': {
            'g_dims': [5, 5],
            'd_dims': [15, 15]
        },
        'train': {
            'k_d': 2,
            'k_g': 1
        }
    }, {
        'gan': {
            'g_dims': [2, 2],
            'd_dims': [12, 12]
        },
        'train': {
            'k_d': 2,
            'k_g': 1
        }
    }]:

        print('START_NEW_PARAMS---------------------------')
        print(params)

        n_examples, input_dim = data.shape
        #gan = GAN(input_dim, g_dims=[50,50], d_dims=[5,5])
        #gan = GAN(input_dim, g_dims=[20,20], d_dims=[10,10])
        gan = GAN(input_dim, g_dims=[2,5], d_dims=[10,10])

        # identify int columns, so we round them later
        int_cols = np.where((df_y.dtypes == np.int64).as_matrix())[0]

        print('Training GAN for year', y)
        print('Samples:', n_examples)
        for samples in gan.train(data, pretrain_epochs=0, epochs=1000, batch_size=1000, k_d=2, k_g=1):
            for col in int_cols:
                round_column(samples, col)
            simulated_df = pd.DataFrame(samples, columns=df_y.columns)
            print(simulated_df.head())

        #samples = gan.generate(100)
        #for col in int_cols:
            #round_column(samples, col)
        #simulated_df = pd.DataFrame(samples, columns=df_y.columns)
        #print(simulated_df)

    break