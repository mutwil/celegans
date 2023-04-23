from flask import Flask, render_template, request, redirect, url_for
import pickle
import re
from Bio import Entrez


def generate_cytoscape_js(elements):
    nodes = [
        "{ data: { id: '%s' } }" % node
        for node in set(edge["source"] for edge in elements) | set(edge["target"] for edge in elements)
    ]
    edges = [
        "{ data: { id: 'edge%s', source: '%s', target: '%s', interaction: '%s' } }" % (
            i,
            edge['source'],
            edge['target'],
            edge['interaction'],
        )
        for i, edge in enumerate(elements)
    ]

    a = open('network.txt','r').read()

    nodes = ', '.join(nodes)
    edges = ', '.join(edges)
    return a.replace('NODES',nodes).replace('EDGES',edges)

def process_network(elements):    
    #remove redundancies
    edges = []
    for i in elements:
        if i not in edges:
            edges.append(i)

    #groups similar nodes that have same source+interaction
    edgeTypes = {}
    for i in elements:
        key = (i['source'], i['interaction'])
        if key in edgeTypes:
            edgeTypes[key] += [i['target']]
        else:
            edgeTypes[key] = [i['target']]
    return edges

def find_terms(my_search, genes):   
    forSending = []
    elements = [] 

    if len(my_search)>0:
        for i in genes:
            if '!' in my_search: #exact search
                if my_search.upper().strip().replace('!','') == i.strip():
                    for j in genes[i]:
                        if j[0]!='' and j[2]!='':
                            forSending.append(Gene(j[0], j[2], j[1], j[3])) #source, target, type
                            elements.append({"source": j[0].replace("'","").replace('"',''), "target": j[2].replace("'","").replace('"',''), "interaction": j[1].replace("'","").replace('"','')})                
            if my_search.upper().strip() in i.strip():
                print(i,'asd')
                for j in genes[i]:
                    if j[0]!='' and j[2]!='':
                        forSending.append(Gene(j[0], j[2], j[1], j[3])) #source, target, type
                        elements.append({"source": j[0].replace("'","").replace('"',''), "target": j[2].replace("'","").replace('"',''), "interaction": j[1].replace("'","").replace('"','')})
    return elements, forSending

app = Flask(__name__)

class Gene:
    def __init__(self, id, description, inter_type, publication):
        self.id = id
        self.target = description
        self.inter_type = inter_type
        self.publication = publication

@app.route('/')
def index():
    v = open('stats.txt','r').read().rstrip().split()

    journals, numbers = open('journal_statistics.txt','r').read().splitlines()
    piechart = open('piechart.txt','r').read()
    piechart = piechart.replace('JOURNALS', journals)
    piechart = piechart.replace('NUMBERS', numbers)

    return render_template('index.html', entities = v[1], papers = v[0], piechart_code = piechart)
    
@app.route('/author', methods=['POST'])
def author():
    try:
        my_search = request.form["author"].lower()
    except:
        my_search=''

    if my_search!='':
        with open('abstracts', 'rb') as f:
            # Load the object from the file
            papers = pickle.load(f)
            
        hits = []
        
        for i in papers:
            for author in i['authors']:
            
                replacements = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "é": "e", "ô": "o", "î": "i", "ç": "c"}
                author = ''.join(replacements.get(c, c) for c in author)

                if len(set(my_search.split())&set(author.lower().split()))==len(set(my_search.split())):
                    hits.append(i['pmid'])
                    
        # provide your email address to the Entrez API
        Entrez.email = "mutwil@gmail.com"

        # search query to find papers by an author
        search_query = my_search+"[Author]"

        # perform the search and retrieve the count of papers
        handle = Entrez.esearch(db="pubmed", term=search_query)
        record = Entrez.read(handle)
        count = record["Count"]
        print(count)
        
        forSending = []
        if hits!=[]:
            with open('allDic', 'rb') as file:
                genes = pickle.load(file)
            
            
            elements = []
            papers = []
            for i in genes:
                for j in genes[i]:
                    if j[3] in hits:
                        if j[0]!='' and j[2]!='':
                            papers.append(j[3])
                            forSending.append(Gene(j[0], j[2], j[1], j[3])) #source, target, type
                            elements.append({"source": j[0].replace("'","").replace('"',''), "target": j[2].replace("'","").replace('"',''), "interaction": j[1].replace("'","").replace('"','')})                
                        break

    
    if forSending!=[]:
        elements = process_network(elements)
        cytoscape_js_code = generate_cytoscape_js(elements)
        warning = ''
        if len(elements)>400:
            warning = 'The network might be too large to be displayed, so click on "Layout Options", select the edge types that you are interested in and click "Recalculate layout".'

        return render_template('author.html', genes=forSending, cytoscape_js_code=cytoscape_js_code, ncbi_count=count, author= my_search, connectome_count=len(set(papers)), warning=warning)
    else:
        return render_template('not_found.html')
        
@app.route('/title', methods=['POST'])
def title():
    try:
        my_search = request.form['title'].lower()
    except:
        my_search=''

    if my_search!='':
        with open('abstracts', 'rb') as f:
            # Load the object from the file
            papers = pickle.load(f)
            
        hits = []
        
        for i in papers:
            if len(set(my_search.split())&set(i['title'].lower().split()))>len(set(my_search.split()))*0.8:
                hits.append(i['pmid'])
                break
        
        forSending = []
        if hits!=[]:
            with open('allDic', 'rb') as file:
                genes = pickle.load(file)
            
            
            elements = [] 
            for i in genes:
                for j in genes[i]:
                    if j[3] in hits:
                        if j[0]!='' and j[2]!='':
                            forSending.append(Gene(j[0], j[2], j[1], j[3])) #source, target, type 
                            elements.append({"source": j[0].replace("'","").replace('"',''), "target": j[2].replace("'","").replace('"',''), "interaction": j[1].replace("'","").replace('"','')})                
                        break

    if forSending!=[]:
        elements = process_network(elements)
        cytoscape_js_code = generate_cytoscape_js(elements)
        return render_template('gene.html', genes=forSending, cytoscape_js_code=cytoscape_js_code)
    else:
        return render_template('not_found.html')

@app.route('/search', methods=['POST'])
def search():
    with open('allDic', 'rb') as file:
        genes = pickle.load(file)

    try:
        my_search = request.form['gene_id']
    except:
        my_search='cesa'
         
    if len(my_search)>0:
        split_search = my_search.split(';')
        
        forSending = []
        elements = []

        for term in split_search:
            results = find_terms(term, genes)
            elements += results[0]
            forSending += results[1]
            
        papers = []
        for i in forSending:
            papers+=[i.publication]
            
        warning = ''
        if len(elements)>400:
            warning = 'The network might be too large to be displayed, so click on "Layout Options",  select the edge types that you are interested in and click "Recalculate layout".'
        elements = process_network(elements)
        cytoscape_js_code = generate_cytoscape_js(elements)

    if forSending!=[]:
        return render_template('gene.html', genes=forSending, cytoscape_js_code=cytoscape_js_code, search_term = my_search, number_papers = len(set(papers)), warning = warning)
    else:
        return render_template('not_found.html')

@app.route('/help')
def help():
    return render_template('help.html')

if __name__ == '__main__':
    import os
    items, edges = [],0
    for i in os.listdir(os.getcwd()+'/annotations/'):
        a = open(os.getcwd()+'/annotations/'+i,'r').read()
        
        if len(a)>0:
            findings = a.split('\n\n')[1].split('\n')
            
            for j in findings:
                if j.count('!')==2:
                    splitta = j.split('!')
        
                    agentA, _, agentB = splitta
                    agentA = agentA.split(':')[0].upper()
                    agentB = agentB.strip().upper()
                    edges+=1
                    items+=[agentA]
                    items+=[agentB]
                
    
    v = open('stats.txt','w')
    v.write(str(len(os.listdir(os.getcwd()+'/annotations/')))+'\t'+str(len(set(items))))
    v.close()
    app.run(debug=True)