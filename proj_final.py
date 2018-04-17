import requests
import json
from bs4 import BeautifulSoup
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.figure_factory as ff
import secrets
import sqlite3


CACHE_FNAME = 'delegates_cache.json'
DBNAME = 'delegates.db'
google_places_key = secrets.google_places_key
dpla_key = secrets.dpla_key

try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents.encode("utf-8"))
    cache_file.close()
except:
    CACHE_DICTION = {}

def get_unique_key(url):
    return url  

def params_unique_combo(baseurl, params_diction): 
    alphabetized_keys = sorted(params_diction.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params_diction[k]))
    return baseurl + "_".join(res)

def BSrequest_using_cache(url):
    unique_ident = get_unique_key(url)
    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]
    else:
        resp = requests.get(url)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[unique_ident]

def api_request(baseurl, params_diction):
    unique_ident = params_unique_combo(baseurl, params_diction)
    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]
    else:
        response_obj = requests.get(baseurl, params=params_diction)
        new_dict=json.loads(response_obj.text)
        CACHE_DICTION[unique_ident] = new_dict
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[unique_ident]

class Dec_Signers():
    def __init__(self, name, state, declaration, articles, constitution):
        self.name = name
        self.state = state
        self.declaration = declaration
        self.articles = articles
        self.constitution = constitution

class Archives():
    def __init__(self, namez, formatz, repository, score):
        self.namez = namez
        self.formatz = formatz
        self.repository = repository
        self.score = score

################################# RETRIEVING DATA / DATABASES #######################################

def get_delegates_data():
    baseurl = 'https://en.wikipedia.org/wiki/List_of_delegates_to_the_Continental_Congress'
    page_text = BSrequest_using_cache(baseurl)
    page_soup = BeautifulSoup(page_text, 'html.parser')

    list_of_names= []
    list_of_states = [] 
    list_of_dec_signers = []
    list_of_art_signers = []
    list_of_con_signers = []

    table = page_soup.find("table", {"class":"wikitable sortable"})
    tr = table.find_all("tr")

    for _tr in tr:
        td = _tr.find_all("td")
        for _td in td:
            a = _td.find_all("a")
            for _a in a:
                ab = _a.text
                if len(ab) > 4:
                    list_of_names.append(ab)

            tds = _td.text

    tablez = page_soup.find("table",class_="wikitable sortable")
    for items in tablez.find_all("tr", )[:-1]:
        data = [' '.join(item.text.split()) for item in items.find_all('td')]  
        if data == []:
            continue
        else:
            states = data[2]
            list_of_states.append(states)

            decl = data[5]
            for each in decl:
                if each =="—":
                    decl = "no"
                    list_of_dec_signers.append(decl)
                else:
                    decl = "yes"
                    list_of_dec_signers.append(decl)

            art = data[6]
            for each in art:
                if each =="—":
                    art = "no"
                    list_of_art_signers.append(art)
                else:
                    art = "yes"
                    list_of_art_signers.append(art)

            con = data[7]
            for each in con:
                if each =="—":
                    con = "no"
                    list_of_con_signers.append(con)
                else:
                    con = "yes"
                    list_of_con_signers.append(con)

        
    class_inst_list = [] #list of class instances 
    for (name, state, declaration, articles, constitution) in zip(list_of_names, list_of_states, list_of_dec_signers, list_of_art_signers, list_of_con_signers):
        x = Dec_Signers(name, state, declaration, articles, constitution)
        class_inst_list.append(x)

    return class_inst_list

def init_db(db_name):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    
    statement = '''
        DROP TABLE IF EXISTS 'DelegatesInfo';  
    '''
    cur.execute(statement)
    statement = '''
        DROP TABLE IF EXISTS 'ArchivalMaterials';
    '''
    cur.execute(statement)
    conn.commit()

    statement1 = '''
        CREATE TABLE 'DelegatesInfo' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Name' TEXT NOT NULL,
                'State' TEXT NOT NULL,
                'Sign_Declaration' TEXT NOT NULL,
                'Sign_Articles' TEXT NOT NULL,
                'Sign_Constitution' TEXT NOT NULL
                
        );
    '''
    cur.execute(statement1)
    statement = '''
        CREATE TABLE 'ArchivalMaterials' (
            'ItemId' INTEGER PRIMARY KEY AUTOINCREMENT,
            'DelegateId' INTEGER NOT NULL,
            'Format' TEXT NOT NULL,
            'Repository' TEXT NOT NULL, 
            'Score' INTEGER NOT NULL,
            FOREIGN KEY ('DelegateId') REFERENCES 'DelegatesInfo(Id)'
        );    
    '''
    cur.execute(statement)
    conn.commit()
    conn.close()

def insert_bio_data():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    signer_data = get_delegates_data()

    for each in signer_data:
        insertion = (None, each.name.replace('"', ''), each.state, each.declaration, each.articles, each.constitution)
        statement = 'INSERT INTO "DelegatesInfo"'
        statement += ' VALUES (?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)

    conn.commit()
    conn.close()

def get_dpla_info():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    get_data = get_delegates_data()
 
    list_of_formats = []
    list_of_repos = []
    list_of_scores = []
    list_of_delegates = []
    class_inst_list = []

    for each in get_data:
        baseurl = 'https://api.dp.la/v2/items'
        params_diction={}
        params_diction["sourceResource.date.before"] = 1800
        params_diction["q"] = each.name
        params_diction["api_key"]= dpla_key

        repo_data = api_request(baseurl, params_diction)
        updated_repo_data = repo_data['docs']
        for x in updated_repo_data:  
            repo_name = x['provider']['name']
            list_of_repos.append(repo_name)
            try:
                if type(x['sourceResource']['format']) == list:
                    format_type = x['sourceResource']['format'][0] #it's gonna give me a list, only can put 1 in the table 
                    list_of_formats.append(format_type)
                else:
                    format_type = x['sourceResource']['format']
                    list_of_formats.append(format_type)
            except:
                format_type = 'N/A'
                list_of_formats.append(format_type)
            score = x['score']  
            list_of_scores.append(float("{0:.2f}".format(score)))
            list_of_delegates.append(each.name)

    for (namez,formatz,repository,score) in zip(list_of_delegates, list_of_formats, list_of_repos, list_of_scores):
        x = Archives(namez.replace('"', ''),formatz,repository,score)
        class_inst_list.append(x)

    return class_inst_list

def insert_archive_data():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    dpla = get_dpla_info()    

    for item in dpla:
        stmt = "SELECT Id "
        stmt += "FROM DelegatesInfo "
        stmt += 'WHERE Name = "' + str(item.namez) + '"'   #not all item.names returned stuff in api
        cur.execute(stmt)
        for x in cur.fetchall():
            y = x[0]
            insertion = (y, item.formatz, item.repository, item.score)
            statement = 'INSERT INTO "ArchivalMaterials" ("ItemId", "DelegateId", "Format", "Repository", "Score")'
            statement += ' VALUES (NULL, ?, ?, ?, ?)'
            cur.execute(statement, insertion)
            conn.commit()
    conn.close()
     

################################# DATA PROCESSING #######################################

def data_processing_delegates():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    delegates = []
    stmt = "SELECT Name "
    stmt += "FROM DelegatesInfo "
    cur.execute(stmt)
    for row in cur:
        delegates.append(row[0])
    return delegates

def data_processing_delegates_state(state):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    delegates = []
    stmt = "SELECT Name "
    stmt += "FROM DelegatesInfo "
    stmt += 'WHERE DelegatesInfo.State = "' + state +'"'
    cur.execute(stmt)
    for row in cur:
        delegates.append(row[0])
    return delegates

def data_processing_state_count():
    #want to get number of signers from each state
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    
    state_count_dic = {}
    stmt = "SELECT State, COUNT(*) "
    stmt += "FROM DelegatesInfo "
    stmt += "GROUP BY State "
    cur.execute(stmt)
    for row in cur:
        state_count_dic[row[0]] = row[1]

    return state_count_dic

def data_processing_sign_which_docs(state):
    #want to get how many of each signing categories fall into 
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    sign_doc = []
    if state != "":
        statement1 = "SELECT Count(*) "
        statement1 += "FROM DelegatesInfo "
        statement1 += 'WHERE Sign_Declaration = "yes" and Sign_Articles = "no" and Sign_Constitution = "no" and DelegatesInfo.State = "' + state + '"'
        cur.execute(statement1)
        for x1 in cur.fetchone():
            sign_doc.append(x1)
            
        statement2 = "SELECT Count(*) "
        statement2 += "FROM DelegatesInfo "
        statement2 += 'WHERE Sign_Declaration = "no" and Sign_Articles = "yes" and Sign_Constitution = "no" and DelegatesInfo.State = "' + state + '"'
        cur.execute(statement2)
        for x2 in cur.fetchone():
            sign_doc.append(x2)
         
        statement3 = "SELECT Count(*) "
        statement3 += "FROM DelegatesInfo "
        statement3 += 'WHERE Sign_Declaration = "no" and Sign_Articles = "no" and Sign_Constitution = "yes" and DelegatesInfo.State = "' + state + '"'
        cur.execute(statement3)
        for x3 in cur.fetchone():
            sign_doc.append(x3)
        
        statement4 = "SELECT Count(*) "
        statement4 += "FROM DelegatesInfo "
        statement4 += 'WHERE Sign_Declaration = "yes" and Sign_Articles = "yes" and Sign_Constitution = "no" and DelegatesInfo.State = "' + state + '"'
        cur.execute(statement4)
        for x4 in cur.fetchone():
            sign_doc.append(x4)
       
        statement5 = "SELECT Count(*) "
        statement5 += "FROM DelegatesInfo "
        statement5 += 'WHERE Sign_Declaration = "yes" and Sign_Articles = "no" and Sign_Constitution = "yes" and DelegatesInfo.State = "' + state + '"'
        cur.execute(statement5)
        for x5 in cur.fetchone():
            sign_doc.append(x5)
         
        statement6 = "SELECT Count(*) "
        statement6 += "FROM DelegatesInfo "
        statement6 += 'WHERE Sign_Declaration = "no" and Sign_Articles = "yes" and Sign_Constitution = "yes" and DelegatesInfo.State = "' + state + '"'
        cur.execute(statement6)
        for x6 in cur.fetchone():
            sign_doc.append(x6)
          
        statement7 = "SELECT Count(*) "
        statement7 += "FROM DelegatesInfo "
        statement7 += 'WHERE Sign_Declaration = "yes" and Sign_Articles = "yes" and Sign_Constitution = "yes" and DelegatesInfo.State = "' + state + '"'
        cur.execute(statement7)
        for x7 in cur.fetchone():
            sign_doc.append(x7)
           
        statement8 = "SELECT Count(*) "
        statement8 += "FROM DelegatesInfo "
        statement8 += 'WHERE Sign_Declaration = "no" and Sign_Articles = "no" and Sign_Constitution = "no" and DelegatesInfo.State = "' + state + '"'
        cur.execute(statement8)
        for x8 in cur.fetchone():
            sign_doc.append(x8)
           

    else:
        statement1 = "SELECT Count(*) "
        statement1 += "FROM DelegatesInfo "
        statement1 += "WHERE Sign_Declaration = 'yes' and Sign_Articles = 'no' and Sign_Constitution = 'no'"
        cur.execute(statement1)
        for x1 in cur.fetchone():
            sign_doc.append(x1)
            
        statement2 = "SELECT Count(*) "
        statement2 += "FROM DelegatesInfo "
        statement2 += "WHERE Sign_Declaration = 'no' and Sign_Articles = 'yes' and Sign_Constitution = 'no'"
        cur.execute(statement2)
        for x2 in cur.fetchone():
            sign_doc.append(x2)
         
        statement3 = "SELECT Count(*) "
        statement3 += "FROM DelegatesInfo "
        statement3 += "WHERE Sign_Declaration = 'no' and Sign_Articles = 'no' and Sign_Constitution = 'yes'"
        cur.execute(statement3)
        for x3 in cur.fetchone():
            sign_doc.append(x3)
        
        statement4 = "SELECT Count(*) "
        statement4 += "FROM DelegatesInfo "
        statement4 += "WHERE Sign_Declaration = 'yes' and Sign_Articles = 'yes' and Sign_Constitution = 'no'"
        cur.execute(statement4)
        for x4 in cur.fetchone():
            sign_doc.append(x4)
       
        statement5 = "SELECT Count(*) "
        statement5 += "FROM DelegatesInfo "
        statement5 += "WHERE Sign_Declaration = 'yes' and Sign_Articles = 'no' and Sign_Constitution = 'yes'"
        cur.execute(statement5)
        for x5 in cur.fetchone():
            sign_doc.append(x5)
         
        statement6 = "SELECT Count(*) "
        statement6 += "FROM DelegatesInfo "
        statement6 += "WHERE Sign_Declaration = 'no' and Sign_Articles = 'yes' and Sign_Constitution = 'yes'"
        cur.execute(statement6)
        for x6 in cur.fetchone():
            sign_doc.append(x6)
          
        statement7 = "SELECT Count(*) "
        statement7 += "FROM DelegatesInfo "
        statement7 += "WHERE Sign_Declaration = 'yes' and Sign_Articles = 'yes' and Sign_Constitution = 'yes'"
        cur.execute(statement7)
        for x7 in cur.fetchone():
            sign_doc.append(x7)
           
        statement8 = "SELECT Count(*) "
        statement8 += "FROM DelegatesInfo "
        statement8 += "WHERE Sign_Declaration = 'no' and Sign_Articles = 'no' and Sign_Constitution = 'no'"
        cur.execute(statement8)
        for x8 in cur.fetchone():
            sign_doc.append(x8)
            
    return sign_doc

def data_processing_avg_ratings(state):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    
    avg_dic = {}
    if state != "":
        stmt = "SELECT DelegatesInfo.Name, AVG(ArchivalMaterials.Score) "
        stmt += "FROM ArchivalMaterials "
        stmt += "JOIN DelegatesInfo "
        stmt += "ON DelegatesInfo.Id = ArchivalMaterials.DelegateId "
        stmt += 'WHERE DelegatesInfo.State = "' + state +'"'
        stmt += "GROUP BY ArchivalMaterials.DelegateId "
    else:
        stmt = "SELECT DelegatesInfo.Name, AVG(ArchivalMaterials.Score) "
        stmt += "FROM ArchivalMaterials "
        stmt += "JOIN DelegatesInfo "
        stmt += "ON DelegatesInfo.Id = ArchivalMaterials.DelegateId "
        stmt += "GROUP BY ArchivalMaterials.DelegateId "
    
    cur.execute(stmt)
    for row in cur:
        avg_dic[row[0]] = float("{0:.1f}".format(row[1]))

    return avg_dic

def data_processing_repository_count():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    
    repo_count_dic = {}
    stmt = "SELECT Repository, COUNT(*) "
    stmt += "FROM ArchivalMaterials "
    stmt += "GROUP BY Repository "
    cur.execute(stmt)
    for row in cur:
        repo_count_dic[row[0]] = row[1]

    conn.close()

    return repo_count_dic

################################# VISUALS #######################################

def graph_state():
    state_dic = data_processing_state_count()
    dic_keys_list = list(state_dic.keys())
    dic_values_list = list(state_dic.values())

    data = [go.Bar(
                x=dic_keys_list,
                y=dic_values_list,
                text=dic_values_list,
                textposition = 'auto',
                marker=dict(
                    color='rgb(158,202,225)',
                    line=dict(
                        color='rgb(8,48,107)',
                        width=1.5),
                ),
                opacity=0.8
            )]

    layout = go.Layout(
        title='Number of Delegates by State Represented',
        xaxis=dict(
            title='States Delegates Represented'
        ),
        yaxis=dict(
            title='Count'
        ),
        bargap=0.1,
        bargroupgap=0.1
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='styled histogram')


def graph_repositories():
    orig_dic = data_processing_repository_count()
    z = sorted(orig_dic.items(), key=lambda x: x[1], reverse=True)
    repo_dic = {}
    for each in z:
        repo_dic[each[0]] = each[1]

    dic_keys_list = list(repo_dic.keys())
    dic_values_list = list(repo_dic.values())
    append_key_list = []
    for each in dic_keys_list:
        if len(each) > 20:
            each = each[:20] + "..."
            append_key_list.append(each)
        else:
            append_key_list.append(each)
    
    data = [go.Bar(
                x=append_key_list,
                y=dic_values_list,
                text=dic_values_list,
                textposition = 'auto',
                marker=dict(
                    color='rgb(158,202,225)',
                    line=dict(
                        color='rgb(8,48,107)',
                        width=1.0),
                ),
                opacity=0.8
            )]

    layout = go.Layout(
        title='Frequency of Repositories for Delegates',
        xaxis=dict(
            title='Repositories'
        ),
        yaxis=dict(
            title='Count'
        ),
        bargap=0.1,
        bargroupgap=0.1
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='styled histogram')


def pie_chart_sign_docs(state):
    if state == "":
        x = data_processing_sign_which_docs(state)
    else:
        x = data_processing_sign_which_docs(state)
        
    labels = ['Signed Declaration','Signed Articles','Signed Constitution','Signed Declaration and Articles', 'Signed Declaration and Constitution', 'Signed Articles and Constitution', 'Signed All 3', 'Signed None']
    values = x
    colors = ['#ff0000', '#ff6600', '#ffff00', '#33cc33', '#1affff', '#0066cc', '#9900ff', '#ff3399']

    trace = go.Pie(labels=labels, values=values,
               hoverinfo='label+percent', textinfo='value', 
               textfont=dict(size=15), sort=False, 
               marker=dict(colors=colors, 
                           line=dict(color='#000000', width=3)))

    py.plot([trace], filename='styled_pie_chart')

def graph_scores(state):
    if state == "":
        y = data_processing_avg_ratings(state)
    else: 
        y = data_processing_avg_ratings(state)
    z = sorted(y.items(), key=lambda x: x[1], reverse=True)

    avg_dic = {}
    for each in z:
        avg_dic[each[0]] = each[1]
    avg_keys_list = list(avg_dic.keys())
    avg_values_list = list(avg_dic.values())


    data = [go.Bar(
    x = avg_keys_list, 
    y= avg_values_list,
    text= avg_values_list,
    textposition = 'auto',
    marker=dict(
        color='rgb(158,202,225)',
        line=dict(
            color='rgb(8,48,107)',
            width=1.5),
        ),
    opacity=0.6
    )]

    layout = go.Layout(
        barmode='group'
    )

    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='grouped-bar')


def load_help_text():
    with open('help.txt') as f:
        return f.read()

################################# INTERACTIVE #######################################

if __name__=="__main__":
    init_db(DBNAME)
    insert_bio_data()
    insert_archive_data()

    def interactive_prompt():
        help_text = load_help_text()
        response = ''
        while response != 'exit':
            response = input('Enter a command: ')
            x = response

            if "delegates" in x:
                if len(x) == 14 and "list" in x:
                    y = data_processing_delegates()
                    for each in y:
                        print(each)
                elif len(x) > 14 and "list" in x:
                    y = data_processing_delegates_state(x[15:])
                    for each in y:
                        print(each)
                elif "chart" in x:
                    graph_state()
                else:
                    print("Bad Command")
                    continue

            elif "signed" in x:
                if len(x) == 12 :
                    state = ''
                    pie_chart_sign_docs(state)
                elif len(x) > 12:
                    state = x[13:]
                    pie_chart_sign_docs(state)

                elif "chart" not in x:
                    print("Bad Command")
                 
                else:
                    print("Bad Command")
                    
            elif "scores" in x:
                if len(x) == 12 :
                    state = ''
                    graph_scores(state)
                elif len(x) > 12:
                    state = x[13:]
                    graph_scores(state)

                elif "chart" not in x:
                    print("Bad Command")
                else:
                    print("Bad Command")

            elif "repos" in x:
                if "chart" in x:
                    graph_repositories()
                elif "list" in x:
                    y = data_processing_repository_count()  #dictionary with {Repo Name: Count}
                    z = sorted(y.items(), key=lambda x: x[1], reverse=True)

                    for each in z:
                        if each[1] == 1:
                            print("{}: {} item".format(each[0], each[1]))
                        else:
                            print("{}: {} items".format(each[0], each[1]))


                elif "list" not in x and "chart" not in x:
                    print("Bad Command")
                    
                else:
                    print("Bad Command")
            
            elif "help" in x:
                print(help_text)
               
            elif "exit" not in x and "help" not in x and "repos" not in x and "scores" not in x and "delegates" not in x and "signed" not in x: 
                print("Bad Command")

            print("-----------------------------------------------")
        print('Goodbye!')

    interactive_prompt()











