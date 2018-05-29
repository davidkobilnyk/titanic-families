'''Scripts to save relationships and family trees to csv.
'''

from data import TitanicDataSet
from findfamilies import construct_family_components
import pandas as pd

def main():
    create_relationship_dfs()

def df_with_new_row(df, row):
    row.name = len(df) + 1
    df = df.append(row)
    return df

def df_with_new_relationship(df, person1, person2, rel_name):
    return df_with_new_row(df, pd.Series({
        'PassengerId1': person1.a.passenger_id,
        'PassengerId2': person2.a.passenger_id,
        'RelationshipType': rel_name,
        'Survived1': float('nan') if pd.isnull(person1.survived) else person1.survived,
        'Survived2': float('nan') if pd.isnull(person2.survived) else person2.survived,
    }))

def create_relationship_dfs():
    train = TitanicDataSet.get_train()
    test = TitanicDataSet.get_test()
    families = construct_family_components(train, test)
    families = sorted(families, key=lambda f: len(f.nodes))
    df_rel = pd.DataFrame(
        columns=['PassengerId1', 'PassengerId2', 'RelationshipType', 'Survived1', 'Survived2']
    )
    df_fam = pd.DataFrame(columns=range(1, 18))
    df_fam_membership = pd.DataFrame(columns=['PassengerId', 'FamilyId'])
    for f in families:
        fam_list = [n.a.passenger_id for n in f.nodes]
        fam_dict = dict(zip(range(1, 18), fam_list))
        fam_dict['FamilySize'] = len(f.nodes)
        fam_series = pd.Series(fam_dict)
        df_fam = df_with_new_row(df_fam, fam_series)
        for n in f.nodes:
            series_fam_membership = pd.Series({
                'PassengerId': n.a.passenger_id,
                'FamilyId': len(df_fam)
            })
            df_fam_membership = df_with_new_row(df_fam_membership, series_fam_membership)
            if n.spouse is not None:
                df_rel = df_with_new_relationship(df_rel, n, n.spouse, 'Spouse')
            if n.mother is not None:
                df_rel = df_with_new_relationship(df_rel, n, n.mother, 'Mother')
            if n.father is not None:
                df_rel = df_with_new_relationship(df_rel, n, n.father, 'Father')
            for child in n.children:
                if child.a.sex == 0:
                    df_rel = df_with_new_relationship(df_rel, n, child, 'Son')
                else:
                    df_rel = df_with_new_relationship(df_rel, n, child, 'Daughter')
            for sibling in n.siblings:
                if sibling.a.sex == 0:
                    df_rel = df_with_new_relationship(df_rel, n, sibling, 'Brother')
                else:
                    df_rel = df_with_new_relationship(df_rel, n, sibling, 'Sister')
            for extended in n.extendeds:
                df_rel = df_with_new_relationship(df_rel, n, extended, 'Extended')

    df_rel = (df_rel
              .sort_values(by=['PassengerId1', 'PassengerId2'])
              .reset_index()
              .drop('index', axis=1)
             )
    df_rel.index.name = 'RelationshipId'
    df_fam.index.name = 'FamilyId'
    df_fam_membership = df_fam_membership.sort_values(
        by='PassengerId').set_index('PassengerId')
    filename_path_rel = 'data/csv/relationships.csv'
    filename_path_fam = 'data/csv/families.csv'
    filename_path_fam_mem = 'data/csv/family_membership.csv'
    df_rel.to_csv(filename_path_rel)
    df_fam.to_csv(filename_path_fam)
    df_fam_membership.to_csv(filename_path_fam_mem)
    print('saved to %s and %s and %s' % (
        filename_path_rel, filename_path_fam, filename_path_fam_mem
    ))

__name__ == '__main__' and main()
