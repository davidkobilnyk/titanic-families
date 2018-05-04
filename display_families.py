'''Scripts to display family trees using dot
'''

import os
import os.path
from subprocess import check_call

from data import TitanicDataSet
from findfamilies import construct_family_components, DotCreator

import pandas as pd


OUTPUT_DIR = 'families_graphs'
DOT_TMP_PATH = '/tmp/families_graph_tmp.dot'
DOT_SCRIPT = './dotpack.sh'
MAX_FILE_NODES = 100

def main():
    create_relationship_dfs()

def create_graphs():
    train = TitanicDataSet.get_train()
    test = TitanicDataSet.get_test()
    families = construct_family_components(train, test)
    families = sorted(families, key=lambda f: len(f.nodes))

    acc = []
    i = 0
    for c in families:
        #print(len(c.nodes))
        if len(c.nodes) == 1:
            continue
        #if not any(n.a.age == -1 for n in c.nodes):
        #    continue
        #if not c.difficult_parent_child:
        #    continue
        if sum(len(c.nodes) for c in acc) > MAX_FILE_NODES:
            display_graph(i, acc)
            i += 1
            acc = []
        acc.append(c)
    if acc:
        display_graph(i, acc)

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
    df_fam = pd.DataFrame(columns=range(1, 17))
    df_fam_membership = pd.DataFrame(columns=['PassengerId', 'FamilyId'])
    for f in families:
        fam_list = [n.a.passenger_id for n in f.nodes]
        fam_dict = dict(zip(range(1, 17), fam_list))
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
    df_rel = df_rel.sort_values(
        by=['PassengerId1', 'PassengerId2']).reset_index().drop('index', axis=1)
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

def plot_troubled_families():
    """Show the graphs that couldn't be broken down int families
    """
    train = TitanicDataSet.get_train()
    test = TitanicDataSet.get_test()
    families = construct_family_components(train, test)
    families = sorted(families, key=lambda f: len(f.nodes))
    generate_graph('trouble.png', [f for f in families
                                   if f.difficult_parent_child])

def display_graph(i, components):
    print('displaying', i)
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    output_path = os.path.join(OUTPUT_DIR, '%d.png' % (i,))
    generate_graph(output_path, components)

def generate_graph(output_path, components):
    with open(DOT_TMP_PATH, 'w') as fp:
        dc = DotCreator(fp)
        #dc.show_extended = False
        dc.write_components(components,
                            individual_digraphs=True,
                            show_nuclear_families=False)
    ncols = determine_ncols(components)
    check_call([DOT_SCRIPT, DOT_TMP_PATH, str(ncols), output_path])

def determine_ncols(components):
    largest_component = max(len(c.nodes) for c in components)
    if largest_component > 8:
        return 3
    elif largest_component > 5:
        return 4
    elif largest_component > 3:
        return 6
    elif largest_component > 1:
        return 8
    return 10

__name__ == '__main__' and main()
