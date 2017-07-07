import unittest
import json
from kit_test_helper import TestHelper
from bit_extension import BitExtension
# selenium stuff
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.select import Select

# Kit Tree
class KitTreeTestCase(unittest.TestCase):
	filename = None
	CONST_HOST = None

	def setUp(self):
		self.browser = webdriver.Firefox()

	def getTestCase(self, file_path):
		with open(file_path) as data_file:
			data = json.load(data_file)
		return data

	def runTest(self):
		helper = TestHelper()
		helper.dbEstablishConnection()
		if helper.dbTestConnection() == False:
			return

		data = self.getTestCase("json_test_cases/"+self.filename)
		existing, existing_lookup, matching, matching_lookup = data["existing"]["list"], data["existing"]["lookup"], data["matching"]["kit_tree"], data["matching"]["lookup"]
		# self.prepareTest(existing, existing_lookup, helper)

		print("--"*5, "BEGIN TEST ALL", "--"*5)
		for i in matching:
			self.search(i["pn"], i["revision_name"])
			self.checkKitNavigation(i["kit_navigation"])
			self.checkParentNavigation(i["parent_navigation"])
			self.checkMasterNavigation(i["master_navigation"])
			self.checkMainGrid(i["gridview"])
		print("--"*5, "BEGIN TEST DIRECT", "--"*5)
		for i in matching:
			self.search(i["pn"], i["revision_name"], type="DIRECT")
			self.checkKitNavigation(i["kit_navigation"], type="DIRECT")
			self.checkParentNavigation(i["parent_navigation"])
			self.checkMasterNavigation(i["master_navigation"])
			self.checkMainGrid(i["direct_gridview"], type="DIRECT")
		print("--"*5, "BEGIN TEST DROPDOWN CHANGE", "--"*5)
		self.checkRevisionDropDownChanged(matching[len(matching)-2], matching[len(matching)-1])
		self.checkRevisionDropDownChanged(matching[len(matching)-2], matching[len(matching)-1], type="DIRECT")

		helper.dbCloseConnection()

	def prepareTest(self, existing, existing_lookup, helper):
		helper.prepareTest()
		print("***SETTING UP EXISTING DATA IN KIT LIST***")
		for kitlist in existing:
			helper.insertKitList(kitlist["pn"], kitlist["master_pn"], kitlist["parent_pn"], kitlist["revision"], kitlist["subkit_revision"], kitlist["qty"], kitlist["uom"], kitlist["is_kit"], kitlist["description"])
		for lookup in existing_lookup:
			helper.insertKitLookup(lookup["subkit_pn"], lookup["master_pn"], lookup["subkit_revision"], lookup["master_revision"])
		print("***DONE SETTING UP EXISTING DATA***")

	def search(self, pn, revision, type="ALL"):
		print(pn, revision)
		self.browser.get(self.CONST_HOST+"UApplication3/wh/kitrec/kit_tree.aspx")
		wait = WebDriverWait(self.browser, 10)
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txt_PN")))
		kitPN = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_txt_PN")
		if type == "ALL":
			kitPN.send_keys(str(pn) + Keys.RETURN)
		else:
			kitPN.send_keys(str(pn))
			wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_btn_searchDirect")))
			self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_searchDirect").click()
		wait.until(EC.invisibility_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_img_loading")))
		self.searchStep1(pn, revision, wait)

	def searchStep1(self, pn, revision, wait):
		try:
			wait.until(lambda driver: self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_pnl_candidates").is_displayed() or self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_searchAll").is_enabled())
		except Exception:
			self.searchStep1(pn, revision, wait)
			return
		try:
			if not self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_pnl_candidates").is_displayed():
				raise Exception("")
			wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_CandidatesGridView")))
			revision_qs = "&revision="+str(BitExtension().revisionNameToLong(revision)) if revision != "All" and revision != "ALL" else ""
			self.browser.find_element_by_css_selector("table#ctl00_ContentPlaceHolder1_CandidatesGridView.MyDataGridCaption tr.gridBody[onclick*='kit_tree.aspx?pn="+pn+revision_qs+"']").click()
			if revision_qs != "":
				self.checkRevisionDropDown(wait)
				Select(self.browser.find_element_by_css_selector("select#ctl00_ContentPlaceHolder1_ddl_kitRevision")).select_by_value(str(BitExtension().revisionNameToLong(revision)))
				wait.until(EC.invisibility_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_img_loading")))
				wait.until(lambda driver: self.browser.find_element_by_css_selector("select#ctl00_ContentPlaceHolder1_ddl_kitRevision option[value='"+str(BitExtension().revisionNameToLong(revision))+"']").is_selected())
		except Exception as e:
			self.checkRevisionDropDown(wait)
			Select(self.browser.find_element_by_css_selector("select#ctl00_ContentPlaceHolder1_ddl_kitRevision")).select_by_value(str(BitExtension().revisionNameToLong(revision)))
			wait.until(EC.invisibility_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_img_loading")))
			wait.until(lambda driver: self.browser.find_element_by_css_selector("select#ctl00_ContentPlaceHolder1_ddl_kitRevision option[value='"+str(BitExtension().revisionNameToLong(revision))+"']").is_selected())

	def checkRevisionDropDown(self, wait):
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddl_kitRevision")))
		self.assertTrue(self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_ddl_kitRevision").is_displayed(), msg="kit revision ddl not displayed")

	def checkRevisionDropDownChanged(self, child1, child2, type="ALL"):
		if len(child1["kit_navigation"]["children"]) > 0 and len(child2["kit_navigation"]["children"]) > 0 and child1["pn"] == child2["pn"]:
			wait = WebDriverWait(self.browser, 10)
			self.search(child1["pn"], child1["revision_name"], type=type)
			self.checkRevisionDropDown(wait)
			print("SWITCH TO", child2["pn"], child2["revision_name"])
			Select(self.browser.find_element_by_css_selector("select#ctl00_ContentPlaceHolder1_ddl_kitRevision")).select_by_value(str(BitExtension().revisionNameToLong(child2["revision_name"])))
			wait.until(EC.invisibility_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_img_loading")))
			wait.until(lambda driver: self.browser.find_element_by_css_selector("select#ctl00_ContentPlaceHolder1_ddl_kitRevision option[value='"+str(BitExtension().revisionNameToLong(child2["revision_name"]))+"']").is_selected())
			if type == "ALL":
				self.checkMainGrid(child2["gridview"])
			else:
				self.checkMainGrid(child2["direct_gridview"])

	def checkMainGrid(self, children, type="ALL"):
		print("--"*5, "CHECK MAIN GRID", "--"*5)
		testChildren = []
		for child in children:
			if child["is_kit"] != "1" or type == "DIRECT":
				testChildren.append(child)
		rows = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MainGridView.MyDataGridCaption tbody tr.gridBody")
		self.assertEqual(len(rows), len(testChildren), msg="MainGridView: Number of children shown does not match test children")
		matchAllChildren = True
		for row in rows:
			pn = row.find_element_by_css_selector("td:nth-child(1)").text
			quantity = row.find_element_by_css_selector("td:nth-child(2)").text
			uom = row.find_element_by_css_selector("td:nth-child(3)").text
			is_kit = "1" if row.find_element_by_css_selector("input[type='checkbox']").is_selected() else "0"
			description = row.find_element_by_css_selector("td:nth-child(5)").text
			childMatched = False
			index = 0
			for child in testChildren:
				if child["pn"] == pn and child["qty"] == quantity and child["uom"] == uom and child["is_kit"] == is_kit and child["description"] == description:
					print("===", child["pn"], "matched")
					del testChildren[index]
					childMatched = True
					break
				index += 1
			if not childMatched:
				print(pn, quantity, uom, is_kit, description)
				matchAllChildren = False
				break
		self.assertTrue(matchAllChildren, msg="MainGridView: Not every children matches!")
		self.assertTrue(len(testChildren) == 0, msg="MainGridView: Not every children is displayed!")

	def checkKitNavigation(self, tree, type="ALL"):
		print("--"*5, "CHECK KIT NAVIGATION", "--"*5)
		levels = ""
		string = "div#ctl00_ContentPlaceHolder1_tree_kitNavigation > div "+levels+"> table > tbody > tr > td > a"
		if type != "ALL":
			string = "div#ctl00_ContentPlaceHolder1_tree_kitNavigation "+levels+"> table > tbody > tr > td > a"
		stack = []
		stack.append(tree)
		while len(stack) > 0:
			print("Testing level:", len(levels.split("> div ")))
			for x in range(len(stack)):
				current = stack.pop(0)
				for i in current["children"]:
					stack.append(i)
			
			rows = self.browser.find_elements_by_css_selector(string)
			tree_level = []
			for row in rows:
				if row.get_attribute("textContent") != "" and row.get_attribute("textContent") != "[Edit]":
					tree_level.append((row.get_attribute("textContent"), row.get_attribute("href")))

			self.assertEqual(len(stack), len(tree_level))
			matchAllChildren = True
			for child in stack:
				childMatched = False
				index = 0
				for (td, href) in tree_level:
					if child["pn"] == td and str(BitExtension().revisionNameToLong(child["revision_name"])) in href:
						childMatched = True
						print("===", child["pn"], "matched")
						del tree_level[index]
					index += 1
				if not childMatched:
					print("Missing", child["pn"], child["revision_name"])
					matchAllChildren = False
					break
			self.assertTrue(matchAllChildren, msg="kitNavigation: Not every children matches!")
			self.assertTrue(len(tree_level) == 0, msg="kitNavigation: Not every children is displayed!")

			levels = levels + "> div "
			string = "div#ctl00_ContentPlaceHolder1_tree_kitNavigation > div "+levels+"> table > tbody > tr > td > a"

			if type == "DIRECT":
				break

	def checkParentNavigation(self, parents):
		print("--"*5, "CHECK PARENT NAVIGATION", "--"*5)
		testParents = []
		for i in parents:
			testParents.append(i)
		element = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_tree_parent")
		rows = element.find_elements_by_css_selector("div a")
		self.assertEqual(len(rows), len(testParents), msg="parentNavigation: wrong number of parents displayed")
		matchAllParents = True
		for row in rows:
			parentMatched = False
			index = 0
			for parent in testParents:
				if row.get_attribute("textContent") == parent["pn"] and str(BitExtension().revisionNameToLong(parent["revision_name"])) in row.get_attribute("href"):
					parentMatched = True
					print("===", parent["pn"], "matched")
					del testParents[index]
					break
				index += 1
			if not parentMatched:
				print("Missing", row.get_attribute("textContent"))
				matchAllParents = False
				break
		self.assertTrue(matchAllParents, msg="parentNavigation: Not every parent matches!")
		self.assertTrue(len(testParents) == 0, msg="parentNavigation: Not every parent is displayed!")

	def checkMasterNavigation(self, masters):
		print("--"*5, "CHECK MASTER NAVIGATION", "--"*5)
		testMasters = []
		for i in masters:
			testMasters.append(i)
		element = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_tree_master")
		rows = element.find_elements_by_css_selector("div a")
		self.assertEqual(len(rows), len(testMasters), msg="masterNavigation: wrong number of masters displayed")
		matchAllMasters = True
		for row in rows:
			masterMatched = False
			index = 0
			for master in testMasters:
				if row.get_attribute("textContent") == master["pn"] and str(BitExtension().revisionNameToLong(master["revision_name"])) in row.get_attribute("href"):
					masterMatched = True
					print("===", master["pn"], "matched")
					del testMasters[index]
					break
				index += 1
			if not masterMatched:
				print("Missing", row.get_attribute("textContent"))
				matchAllMasters = False
				break
		self.assertTrue(matchAllMasters, msg="masterNavigation: Not every master matches!")
		self.assertTrue(len(testMasters) == 0, msg="masterNavigation: Not every master is displayed!")