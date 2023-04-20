from flask import Flask, render_template, request, redirect, url_for
import pickle

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
    print(edgeTypes)
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
                        elements.append({"source": j[0].replace("'","").replace('"',''), "target": j[2].replace("'","").replace('"',''), "interaction": j[1]})
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
    return render_template('index.html', entities = v[1], papers = v[0])

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


        elements = process_network(elements)
        cytoscape_js_code = generate_cytoscape_js(elements)
    if forSending!=[]:
        return render_template('gene.html', genes=forSending, cytoscape_js_code=cytoscape_js_code)
    else:
        return render_template('not_found.html')

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