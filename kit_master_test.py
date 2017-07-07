import unittest
from kit_receiving_test import KitReceivingTestCase
from kit_tree_test import KitTreeTestCase
from kit_edit_test import KitEditTestCase
from kit_missing_test import MissingKitTestCase

if __name__ == "__main__":
	suite = unittest.TestSuite()
	edit = KitEditTestCase()
	edit.CONST_HOST = "http://localhost:58363/"
	# suite.addTest(edit)
	missing = MissingKitTestCase()
	missing.CONST_HOST = "http://localhost:58363/"
	# suite.addTest(missing)
	# for i in ["test1.json", "test2.json", "test3.json", "test4.json", "test5.json", "test6.json", "test7.json"]:
	# for i in ["test5.json", "test6.json", "test7.json"]:
	for i in ["test1.json"]:
		receiving = KitReceivingTestCase()
		tree = KitTreeTestCase()
		receiving.filename = i
		receiving.CONST_HOST = "http://localhost:58363/"
		tree.filename = i
		tree.CONST_HOST = "http://localhost:58363/"
		suite.addTest(receiving)
		suite.addTest(tree)
	unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)