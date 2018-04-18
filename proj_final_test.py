import unittest
from proj_final import *

class TestAccess(unittest.TestCase):
    def setUp(self):
        self.state = get_delegates_data()
        self.repository = get_dpla_info()


    def test_delegates(self):
        x = get_delegates_data()
        self.assertEqual(len(x), 344)
        self.assertEqual(len(self.state), 344)
        self.assertTrue(self.state, 'Virginia')
        self.assertNotIn('Michigan', self.state)
    
    def test_dpla(self):
        x = get_dpla_info()
        self.assertEqual(len(x), 2957)
        self.assertTrue(self.repository, "The New York Public Library")
        self.assertNotIn("William L. Clements Library", self.repository)


class TestDatabase(unittest.TestCase):

    def test_DelegatesInfo_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = 'SELECT Name FROM DelegatesInfo '
        results = cur.execute(sql)
        result_list = results.fetchall()

        self.assertIn(('Andrew Adams',), result_list)
        self.assertEqual(len(result_list), 344)

        sql = '''
            SELECT Name, State, Sign_Declaration
            FROM DelegatesInfo
            WHERE State="Connecticut"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 20)
        self.assertEqual(result_list[19][2], 'yes')

        conn.close()


    def test_ArchivalMaterials_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT Format
            FROM ArchivalMaterials
            WHERE Repository="ARTstor"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Bookplates',), result_list)
        self.assertEqual(len(result_list), 23)

        sql = '''
            SELECT COUNT(*)
            FROM ArchivalMaterials
        '''
        results = cur.execute(sql)
        count = results.fetchone()[0]
        self.assertEqual(count, 2977)

        conn.close()


class TestDateProcessing(unittest.TestCase):

    def test_data_processing_delegates(self):
        x = data_processing_delegates()
        self.assertEqual(len(x), 344)
        self.assertEqual(type(x), list)
        self.assertIn("John Alsop", x)

    def test_data_processing_delegates_state(self):
        x = data_processing_delegates_state('Massachusetts')
        self.assertIn("John Adams", x)
        self.assertNotIn("Andrew Adams", x)
        self.assertEqual(type(x), list)

    def test_data_processing_state_count(self):
        x = data_processing_state_count()
        y = list(x.keys())
        self.assertEqual(x["Delaware"], 17)
        self.assertEqual(len(y), 13)

    def test_data_processing_sign_which_docs(self):
        x = data_processing_sign_which_docs("Virginia")
        self.assertEqual(x[0], 6)
        self.assertEqual(x[1], 8)

    def test_data_processing_avg_ratings(self):
        x = data_processing_avg_ratings("New York")
        self.assertEqual(x["John Alsop"], 2.2)
        y = data_processing_avg_ratings("New Jersey")
        self.assertEqual(y["John Stevens"], 5.2)


    def test_data_processing_repository_count(self):
        x = data_processing_repository_count()
        self.assertEqual(x["Smithsonian Institution"], 129)
        y = list(x.keys())
        self.assertEqual(len(y), 29)


class TestVisuals(unittest.TestCase):

    def test_graph_state(self):
        try:
            graph_state()
        except:
            self.fail()

    def test_graph_repositories(self):
        try:
            graph_repositories()
        except:
            self.fail()

    def test_pie_chart_sign_docs(self):
        x = pie_chart_sign_docs("Pennsylvania")
        try:
            x
        except:
            self.fail()

        y = pie_chart_sign_docs('')
        try:
            y
        except:
            self.fail()

    def test_graph_scores(self):
        x = graph_scores("Rhode Island")
        try:
            x
        except:
            self.fail()

        y = graph_scores('')
        try:
            y
        except:
            self.fail()


if __name__ == '__main__':
    unittest.main()
