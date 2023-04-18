
from flask import Flask, render_template, request, redirect, url_for
import pickle

def generate_cytoscape_js(elements):
    nodes = [
        "{ data: { id: '%s' } }" % node.replace("'", r"\'")
        for node in set(edge["source"] for edge in elements) | set(edge["target"] for edge in elements)
    ]
    edges = [
        "{ data: { id: 'edge%s', source: '%s', target: '%s', interaction: '%s' } }" % (
            i,
            edge['source'].replace("'", r"\'"),
            edge['target'].replace("'", r"\'"),
            edge['interaction'].replace("'", r"\'"),
        )
        for i, edge in enumerate(elements)
    ]

    script = f"""
    document.addEventListener('DOMContentLoaded', function () {{
      const cy = cytoscape({{
        container: document.getElementById('cy'),
    
        elements: [
          // Nodes
          {', '.join(nodes)},
    
          // Edges
          {', '.join(edges)}
        ],
    
        style: [
          {{
            selector: 'node',
            style: {{
              'background-color': '#6FB1FC', // Node background color
              'label': 'data(id)',
              'color': '#000000', // Node label text color
              'text-opacity': 1, // Node label text opacity (0-1)
              'font-size': '6px',
              'text-halign': 'center',
              'text-valign': 'center',
              'text-wrap': 'wrap',
              'text-max-width': 50
            }},
          }},
    
          {{
            selector: 'edge',
            style: {{
              'width': 2,
              'line-color': '#A9A9A9', // Edge line color
              'curve-style': 'bezier', // Edge curve style
              'target-arrow-color': '#ccc',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'label': 'data(interaction)',
              'font-size': '6px',
              'text-wrap': 'wrap', // Enable edge label text wrapping
              'text-max-width': 50, // Maximum edge label text width before wrapping (in pixels)
              'text-rotation': 'autorotate',
              'text-margin-x': '5px',
              'text-margin-y': '-5px'
            }},
          }},
        ],
    
        layout: {{
          name: 'cose'
        }}
      }});

    }}
    );
    """
    return script

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
         
    forSending = []
    elements = []
    
    if len(my_search)>0:
        for i in genes:
            if my_search.upper() in i:
                for j in genes[i]:
                    if j[0]!='' and j[2]!='':
                        forSending.append(Gene(j[0], j[2], j[1], j[3])) #source, target, type
                        elements.append({"source": j[0], "target": j[2], "interaction": j[1]})

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
                
        
    # with open('C. elegans[Organism]_papers.txt', 'rb') as file:
    #     genes = pickle.load(file)
    # items, papers = 0, []
    # for i in genes:
    #     items+=1
    #     for j in genes[i]:
    #         papers.append(j[3])
    # papers = set(papers)    
    # print(papers)
    
    v = open('stats.txt','w')
    v.write(str(len(os.listdir(os.getcwd()+'/annotations/')))+'\t'+str(len(set(items))))
    v.close()
    app.run(debug=True)