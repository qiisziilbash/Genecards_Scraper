import json
import re

import pandas as pd
from bs4 import BeautifulSoup as bs
import requests


def read_genes_list(address, importance_list):
    gene_data = pd.read_excel(address, sheet_name=0)
    result = {}

    for importance in importance_list:
        genes = gene_data[importance]
        genes = genes.dropna()
        genes_data = {}

        for row in genes:
            if '(' in row:
                name = row.split('(')[0]
                name = name.strip()

                variant = row.split('(')[1]
                variant = variant.strip()
                variant = variant[0:-1]
            else:
                name = row.strip()
                variant = ''

            if name in genes_data.keys():
                if variant:
                    genes_data[name].append(variant)
            else:
                if variant:
                    genes_data[name] = [variant]
                else:
                    genes_data[name] = []

        result[importance] = genes_data
    return result


def get_variant_info(variant):
    url = 'https://www.ncbi.nlm.nih.gov/snp/' + variant
    response = requests.get(url)
    soup = bs(response.content, "html.parser")

    frequencies = []

    freq_tag = soup.find('dt', text='Frequency')
    if freq_tag:
        lines = freq_tag.find_next('dd').find_all(text=re.compile(r"\(*\)"))
        for freq in lines:
            word = re.sub(r'\s', '', freq)
            if not word == ')':
                frequencies.append(word)

    return frequencies


def get_gene_info(gene, variants, headers):
    print(gene)

    result = {}
    url = 'https://www.genecards.org/cgi-bin/carddisp.pl?gene=' + gene

    response = requests.get(url, headers=headers)
    soup = bs(response.content, "html.parser")

    title = 'Entrez Gene Summary for ' + gene + ' Gene'
    h3_tag = soup.find('h3', text=title)

    summary = h3_tag.find_next('p').contents[0]
    result['summary'] = summary
    print('summary:')
    print(summary)

    title = 'Gene Ontology (GO) - Biological Process for ' + gene + ' Gene'
    h3_tag = soup.find('h3', text=title)
    table = h3_tag.find_next('tbody')

    pathways = []
    for tr in table.find_all('tr'):
        for td in tr.find_all('td'):
            for strong in td.find_all('strong'):
                pathways.append(strong.next)

    result['pathways'] = pathways
    print('Pathways:')
    print(pathways)

    h3_tag = soup.find('h3', text=re.compile(r'MalaCards'))
    table = h3_tag.find_next('tbody')

    disorders = []
    for tr in table.find_all('tr'):
        disorder = tr.find_next('a')
        disorders.append(disorder.contents[0])

    result['related_disorders'] = disorders
    print('Related Disorders')
    print(disorders)

    variants_info = {}
    for variant in variants:
        print(variant)

        frequencies = get_variant_info(variant)
        variant_info = {'frequencies': frequencies}
        variants_info[variant] = variant_info

        print(frequencies)

    if variants_info:
        result['variants_info'] = variants_info
    print('===========================')

    return result


def scrape_genes_info(data, importance_list, headers):
    gene_info = {}

    for importance in importance_list:
        genes = data[importance]
        info = {}

        for gene, variants in genes.items():
            info[gene] = get_gene_info(gene, variants, headers)

        gene_info[importance] = info
    return gene_info


def attach_local_data(address, data):
    gene_conditions_data = pd.read_excel(address, sheet_name=0)

    for idx, row in gene_conditions_data.iterrows():
        conditions = []

        for condition in row['conditions'].split(';'):
            conditions.append(condition.strip())

        if row['name'] in data['Pathogenic'].keys():
            data['Pathogenic'][row['name']]['related_conditions'] = conditions
        else:
            print(row['name'] + ': Does not exist in Pathogenic genes list ')

    gene_conditions_data = pd.read_excel(address, sheet_name=1)

    for idx, row in gene_conditions_data.iterrows():
        conditions = []

        for condition in row['conditions'].split(';'):
            conditions.append(condition.strip())

        if row['name'] in data['HM_VUS'].keys():
            data['HM_VUS'][row['name']]['related_conditions'] = conditions
        else:
            print(row['name'] + ': Does not exist in HM_VUS genes list ')

    return data


if __name__ == '__main__':
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
    importance_list = ['HM_VUS', 'Pathogenic', 'None']

    genes = read_genes_list('data/genes_variants.xlsx', importance_list)
    data = scrape_genes_info(genes, importance_list, headers)

    data = attach_local_data('data/genes_conditions.xlsx', data)

    with open('data/data.json', 'w') as fp:
        json.dump(data, fp, indent=4)
