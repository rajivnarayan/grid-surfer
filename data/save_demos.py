import json
"""Save information of demo datasets in JSON format"""

examples = {
            "Anscombe's Quartet" : {'source': 'vega-dataset',
                                    'type': None,
                                    'file': 'anscombe'},
            'Barley Yield': {'source': 'vega-dataset',
                                'type': None,
                                'file': 'barley'},
            'Cars' : {'source': 'vega-dataset',
                                'type': None,
                                'file': 'cars'},
            'Differential Gene Expression' : {
                        'source': 'local-dataset',
                        'type': 'text/csv',
                        'file': 'data/GSE25724_top_table_clean.csv'},
            'GapMinder Health-Income' : {
                        'source': 'local-dataset',
                        'type': 'text/csv',
                        'file': 'data/gapminder-health-income.csv'},
            'Iris Species': {'source': 'vega-dataset', 
                                'type': None,
                                'file' : 'iris'},
            'Palmer Penguins' : {'source': 'local-dataset',
                                'type': 'application/json',
                                'file': 'data/penguins.json'
                                },
                    }

with open('demo_datasets.json', 'wt') as out_file:
    out_file.write(json.dumps(examples, indent=4))