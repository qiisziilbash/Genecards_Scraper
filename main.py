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
            name = row.split('(')[0]
            name = name.strip()

            variant = row.split('(')[1]
            variant = variant.strip()
            variant = variant[0:-1]

            if name in genes_data.keys():
                genes_data[name].append(variant)
            else:
                genes_data[name] = [variant]

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

    variants_info = {}
    for variant in variants:
        print(variant)

        frequencies = get_variant_info(variant)
        variant_info = {'frequencies': frequencies}
        variants_info[variant] = variant_info

        print(frequencies)

    result['variants_inf'] = variants_info
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


if __name__ == '__main__':
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
    importance_list = ['med', 'high']

    genes = read_genes_list('data/genes_variants.xlsx', importance_list)
    data = scrape_genes_info(genes, importance_list, headers)

    with open('data/data.json', 'w') as fp:
        json.dump(data, fp, sort_keys=True, indent=4)
