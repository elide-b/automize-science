import pandas as pd


def load_data(datapath, sheet_name, mice_sheet):
    # Getting the values for the lipids
    df = pd.read_excel(datapath, sheet_name=sheet_name, header=2)
    df.dropna(axis=1, how='all', inplace=True)

    # Getting the genotypes and regions of the mice samples
    df_mice = pd.read_excel(datapath, sheet_name=mice_sheet, header=None).T
    return df, df_mice


def data_cleanup(df, df_mice):
    # Eliminating the 'Internal Standard' samples
    df = df[df['Lipid Class'] != 'Internal Standard']
    # TODO: omega 6 or 3 to remove (DPEA) from all (ask Alain)

    index = df.columns.tolist()
    subjects = []
    lipids = []
    values = []
    regions = []
    genotype = []
    lipid_class = []

    for i, lipid in enumerate(df['Short Name']):
        for j, subject in enumerate(df.columns[4:]):
            if j != 0:
                y = index.index(j)
                subjects.append(subject)
                lipids.append(lipid)
                lipid_class.append(df.iloc[i, 3])
                values.append(df.iloc[i, y])
                regions.append(df_mice.iloc[1, j])
                genotype.append(df_mice.iloc[0, j])
            else:
                pass

    cleaned_values = [float(value) for value in values]

    df_sorted = pd.DataFrame({'Mouse ID': subjects, 'Lipids': lipids, 'Lipid Class': lipid_class, 'Regions': regions,
                              'Genotype': genotype, 'Values': cleaned_values})

    # TODO: -> but then the average Z scores would be different
    # Filter out lipids in the region where they have 3 values missing
    def filter_lipids(df):
        lipid_zero_counts = df.groupby('Lipids')['Values'].apply(lambda x: (x == 0).sum())
        valid_lipids = lipid_zero_counts[lipid_zero_counts < 3].index
        invalid_lipids = lipid_zero_counts[lipid_zero_counts >= 3].index
        valid_df = df[df['Lipids'].isin(valid_lipids)]
        invalid_df = df[df['Lipids'].isin(invalid_lipids)]
        return valid_df, invalid_df

    df_clean = pd.DataFrame()
    df_eliminated = pd.DataFrame()
    for name, group in df_sorted.groupby('Regions'):
        valid_df, invalid_df = filter_lipids(group)
        df_clean = pd.concat([df_clean, valid_df])
        df_eliminated = pd.concat([df_eliminated, invalid_df])

    # Replace zero values with 80% of the minimum value for the corresponding group
    def replace_zero_values(row, data):
        if row['Values'] == 0:
            group_df = data[(data['Lipids'] == row['Lipids']) &
                            (data['Regions'] == row['Regions']) &
                            (data['Genotype'] == row['Genotype']) &
                            (data['Values'] != 0)]
            if not group_df.empty:
                min_value = group_df['Values'].min()
                if min_value != 0:
                    new_value = 0.8 * min_value
                    return new_value
        return row['Values']

    df_clean['Values'] = df_clean.apply(lambda row: replace_zero_values(row, df_clean), axis=

    return df_clean, df_eliminated
