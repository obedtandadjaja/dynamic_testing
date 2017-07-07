import json
import unittest
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

class MissingKitTestCase(unittest.TestCase):
	filename = None
	CONST_HOST = None

	def setUp(self):
		self.browser = webdriver.Firefox()

	def prepareTest(self, helper):
		helper.prepareTest()
		helper.insertMaster("MK", "1", "EA", "1", "1")

	def runTest(self):
		helper = TestHelper()
		helper.dbEstablishConnection()
		if helper.dbTestConnection() == False:
			return
		self.prepareTest(helper)

		PPB = {"pn": "PPB", "uom": "EA", "is_kit": "0", "description": "1", "qty": "1"}
		SKA = {"pn": "SKA", "uom": "EA", "is_kit": "1", "description": "1", "qty": "1"}
		PPC = {"pn": "PPC", "uom": "TN", "is_kit": "0", "description": "2", "qty": "2"}
		SKB = {"pn": "SKB", "uom": "EA", "is_kit": "1", "description": "2", "qty": "2"}

		# run tests here
		self.login()
		self.locateKit(1, "MK")
		self.receiveExtra("PPA", 1, 1, "EA", "0", "1")
		self.doneKittingIncomplete(1, "MK")
		self.testAddLonePP(PPB, helper)
		self.testAddExistingPP(PPB, helper)
		self.testAddLoneKit(SKA, helper)
		self.testAddExistingKit(SKA, helper)
		self.testUpdateLonePP(PPC, 2, helper)
		self.testUpdateLoneKit(SKB, 3, helper)
		self.testUpdateLoneKitToPP(PPB, 3, helper)
		self.testDeletePP(2, helper)
		self.testDeletePP(2, helper)
		self.testAddLoneKit(SKA, helper)
		self.testDeleteKit(2, SKA, helper)

		helper.dbCloseConnection()

	def testAddLonePP(self, node, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.inputMissing(node)
		self.browser.implicitly_wait(2)
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertEqual(len(rows_before)+1, len(rows_after), msg="testAddLonePP: no new record in missing gridview")
		new_record = helper.executeSelect("select top(1) * from kit_list_missing order by klm_auto_key desc")[0]
		self.assertEqual(new_record.pn, node["pn"], msg="testAddLonePP: pn does not match")
		self.assertEqual(new_record.uom, node["uom"], msg="testAddLonePP: uom does not match")
		self.assertEqual(new_record.qty, int(node["qty"]), msg="testAddLonePP: qty does not match")
		self.assertEqual(new_record.description, node["description"], msg="testAddLonePP: description does not match")
		self.assertEqual(new_record.is_kit, False, msg="testAddLonePP: is_kit does not match")

	def testAddExistingPP(self, node, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		db_before = helper.getKitListMissing()
		self.inputMissing(node)
		self.browser.implicitly_wait(2)
		db_after = helper.getKitListMissing()
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertEqual(len(rows_before), len(rows_after), msg="testAddExistingPP: there is new record in missing gridview")
		self.assertEqual(len(db_before), len(db_after), msg="testAddExistingPP: there is new record in missing table")
		WebDriverWait(self.browser, 2).until(EC.alert_is_present())
		alert = self.browser.switch_to.alert
		self.assertTrue("Insert unsuccessful!" in alert.text, msg="testAddExistingPP: alert text does not match")
		alert.accept()
		self.browser.switch_to.window(self.browser.window_handles[0])

	def testAddLoneKit(self, node, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.inputMissing(node)
		self.browser.implicitly_wait(1)
		missing_stm = helper.getMissingLatestSTM()
		self.locateKit(missing_stm, node["pn"])
		self.inputMissing({"pn": "CHILD", "uom": "EA", "is_kit": "0", "description": "THIS IS A CHILD", "qty": "1"})
		self.locateKit(1, "MK")
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertEqual(len(rows_before)+1, len(rows_after), msg="testAddLoneKit: no new record in missing gridview")
		new_record = helper.executeSelect("select top(2) * from kit_list_missing order by klm_auto_key desc")[1]
		self.assertEqual(new_record.pn, node["pn"], msg="testAddLoneKit: pn does not match")
		self.assertEqual(new_record.uom, node["uom"], msg="testAddLoneKit: uom does not match")
		self.assertEqual(new_record.qty, int(node["qty"]), msg="testAddLoneKit: qty does not match")
		self.assertEqual(new_record.description, node["description"], msg="testAddLoneKit: description does not match")
		self.assertEqual(new_record.is_kit, True, msg="testAddLoneKit: is_kit does not match")
		child_record = helper.executeSelect("select top(2) * from kit_list_missing order by klm_auto_key desc")[0]
		self.assertEqual(child_record.parent_pn, node["pn"], msg="testAddLoneKit: parent_pn does not match")

	def testAddExistingKit(self, node, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		db_before = helper.getKitListMissing()
		self.inputMissing(node)
		self.browser.implicitly_wait(2)
		db_after = helper.getKitListMissing()
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertEqual(len(rows_before), len(rows_after), msg="testAddExistingKit: there is new record in missing gridview")
		self.assertEqual(len(db_before), len(db_after), msg="testAddExistingKit: there is new record in missing table")
		WebDriverWait(self.browser, 2).until(EC.alert_is_present())
		alert = self.browser.switch_to.alert
		self.assertTrue("Insert unsuccessful!" in alert.text, msg="testAddExistingKit: alert text does not match")
		alert.accept()
		self.browser.switch_to.window(self.browser.window_handles[0])

	def testUpdateLonePP(self, node, row, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.updateMissing(node, row)
		self.browser.implicitly_wait(2)
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertEqual(len(rows_before), len(rows_after), msg="testUpdateLonePP: no new record in missing gridview")
		new_record = helper.executeSelect("select * from kit_list_missing where pn='"+node["pn"]+"'")[0]
		self.assertEqual(new_record.pn, node["pn"], msg="testUpdateLonePP: pn does not match")
		self.assertEqual(new_record.uom, node["uom"], msg="testUpdateLonePP: uom does not match")
		self.assertEqual(new_record.qty, int(node["qty"]), msg="testUpdateLonePP: qty does not match")
		self.assertEqual(new_record.description, node["description"], msg="testUpdateLonePP: description does not match")
		self.assertEqual(new_record.is_kit, node["is_kit"] == "1", msg="testUpdateLonePP: is_kit does not match")

	def testUpdateExistingPP(self, node, row, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.updateMissing(node, row)
		self.browser.implicitly_wait(2)
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertEqual(len(rows_before), len(rows_after), msg="testUpdateExistingPP: no new record in missing gridview")
		WebDriverWait(self.browser, 2).until(EC.alert_is_present())
		alert = self.browser.switch_to.alert
		self.assertTrue("failed to update record" in alert.text, msg="testUpdateExistingPP: alert text does not match")
		alert.accept()
		self.browser.switch_to.window(self.browser.window_handles[0])

	def testUpdateLoneKit(self, node, row, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.updateMissing(node, row)
		self.browser.implicitly_wait(2)
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertEqual(len(rows_before), len(rows_after), msg="testUpdateLoneKit: no new record in missing gridview")
		new_record = helper.executeSelect("select * from kit_list_missing where pn='"+node["pn"]+"'")[0]
		self.assertEqual(new_record.pn, node["pn"], msg="testUpdateLoneKit: pn does not match")
		self.assertEqual(new_record.uom, node["uom"], msg="testUpdateLoneKit: uom does not match")
		self.assertEqual(new_record.qty, int(node["qty"]), msg="testUpdateLoneKit: qty does not match")
		self.assertEqual(new_record.description, node["description"], msg="testUpdateLoneKit: description does not match")
		self.assertEqual(new_record.is_kit, node["is_kit"] == "1", msg="testUpdateLoneKit: is_kit does not match")
		child_records = helper.executeSelect("select * from kit_list_missing where kit_parent='"+str(new_record.STM_AUTO_KEY)+"'")
		for child in child_records:
			self.assertEqual(child.parent_pn, node["pn"], msg="testUpdateLoneKit: parent_pn not updated")

	def testUpdateExistingKit(self, node, row, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.updateMissing(node, row)
		self.browser.implicitly_wait(2)
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertEqual(len(rows_before), len(rows_after), msg="testUpdateExistingKit: no new record in missing gridview")
		WebDriverWait(self.browser, 2).until(EC.alert_is_present())
		alert = self.browser.switch_to.alert
		self.assertTrue("failed to update record" in alert.text, msg="testUpdateExistingKit: alert text does not match")
		alert.accept()
		self.browser.switch_to.window(self.browser.window_handles[0])

	def testUpdateLoneKitToPP(self, node, row, helper):
		db_before = helper.getKitListMissing()
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.updateMissing(node, row)
		self.browser.implicitly_wait(2)
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertEqual(len(rows_before), len(rows_after), msg="testUpdateLoneKitToPP: no new record in missing gridview")
		new_record = helper.executeSelect("select * from kit_list_missing where pn='"+node["pn"]+"'")[0]
		self.assertEqual(new_record.pn, node["pn"], msg="testUpdateLoneKitToPP: pn does not match")
		self.assertEqual(new_record.uom, node["uom"], msg="testUpdateLoneKitToPP: uom does not match")
		self.assertEqual(new_record.qty, int(node["qty"]), msg="testUpdateLoneKitToPP: qty does not match")
		self.assertEqual(new_record.description, node["description"], msg="testUpdateLoneKitToPP: description does not match")
		self.assertEqual(new_record.is_kit, node["is_kit"] == "1", msg="testUpdateLoneKitToPP: is_kit does not match")
		db_after = helper.getKitListMissing()
		self.assertLess(len(db_after), len(db_before), msg="testUpdateLoneKitToPP: child records not deleted")

	def testDeletePP(self, row, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.deleteMissing(row)
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertLess(len(rows_after), len(rows_before), msg="testDeletePP: rows after is not less than rows before")

	def testDeleteKit(self, row, node, helper):
		rows_before = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.deleteMissing(row)
		rows_after = self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")
		self.assertLess(len(rows_after), len(rows_before), msg="testDeleteKit: rows after is not less than rows before")
		child_rows = helper.executeSelect("select * from kit_list_missing where parent_pn='"+node["pn"]+"'")
		self.assertEqual(len(child_rows), 0, msg="testDeleteKit: child rows not deleted")

	def login(self):
		self.browser.get(self.CONST_HOST+"UApplication3/login.aspx")
		userName = self.browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserName")
		userName.clear()
		userName.send_keys("oTandadjaja")
		password = self.browser.find_element_by_name("ctl00$ContentPlaceHolder1$Password")
		password.clear()
		password.send_keys("asdf")
		login = self.browser.find_element_by_name("ctl00$ContentPlaceHolder1$LoginImageButton")
		login.click()
		current_url = self.browser.current_url
		wait = WebDriverWait(self.browser, 10)
		wait.until(lambda driver: self.browser.current_url != self.CONST_HOST+"UApplication3/login.aspx")
		self.assertNotIn("User Login", self.browser.title)

	def locateKit(self, stm, pn):
		self.browser.get(self.CONST_HOST+"UApplication3/wh/kitrec/kit_receiving.aspx")
		wait = WebDriverWait(self.browser, 10)
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txt_STM")))
		stm_auto_key = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_txt_STM")
		stm_auto_key.send_keys(str(stm))
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_btn_locateKit")))
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_locateKit").click()
		self.locateKitStep1(pn, wait)

	def locateKitStep1(self, pn, wait):
		try:
			wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_btn_locateKit")))
		except Exception:
			self.locateKitStep1(pn, wait)
			return
		try:
			alert = self.browser.switch_to.alert
			self.assertNotEqual("Invalid STM_AUTO_KEY!", alert.text)
			self.assertNotEqual("Invalid STM_AUTO_KEY! Please insert a number!", alert.text)
			alert.accept()
			self.browser.switch_to.window(self.browser.window_handles[0])
			wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txt_kitPN")))
			wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
			self.assertEqual(str(pn), self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_txt_kitPN").get_attribute("value"), msg="PN does not match the STM")
		except Exception as e:
			wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txt_kitPN")))
			wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
			self.assertEqual(str(pn), self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_txt_kitPN").get_attribute("value"), msg="PN does not match the STM")
			return

	def receiveMissing(self, node, parent, bypass=False):
		if bypass:
			self.locateKit(parent["stm_auto_key"], parent["pn"])
		else:
			self.doneKittingIncomplete(parent["stm_auto_key"], parent["pn"])
		self.inputMissing(node, parent)

	def inputMissing(self, node):
		wait = WebDriverWait(self.browser, 10)
		try:
			self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView")
		except Exception:
			self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_importProceed").click()
			self.inputMissing(node)
			return
		rows = len(self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody"))
		add_row = rows+2 if rows > 0 else 3
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_txt_newPN").clear()
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_txt_newPN").send_keys(str(node["pn"]))
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_txt_newQty").clear()
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_txt_newQty").send_keys(str(node["qty"]))
		Select(self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_ddl_newUOM")).select_by_value(str(node["uom"]))
		if node["is_kit"] == "1":
			while not self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_chk_newIsKit").is_selected():
				self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_chk_newIsKit").click()
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_txt_newDescription").clear()
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_txt_newDescription").send_keys(node["description"])
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(add_row)+"_link_add").click()

	def updateMissing(self, node, row):
		wait = WebDriverWait(self.browser, 10)
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_imb_edit").click()
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_imb_update")))
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_txt_editPN")))
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_ddl_editUOM")))
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_chk_editIsKit")))
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_txt_editDescription")))
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_txt_editPN").clear()
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_txt_editPN").send_keys(node["pn"])
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_txt_editQty").clear()
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_txt_editQty").send_keys(str(node["qty"]))
		Select(self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_ddl_editUOM")).select_by_value(str(node["uom"]))
		if self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_chk_editIsKit").is_selected() != (node["is_kit"] == "1"):
			while (node["is_kit"] == "1") != self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_chk_editIsKit").is_selected():
				self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_chk_editIsKit").click()
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_txt_editDescription").clear()
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_txt_editDescription").send_keys(str(node["description"]))
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_imb_update").click()
		wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))

	def deleteMissing(self, row):
		wait = WebDriverWait(self.browser, 10)
		rows = len(self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody"))
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView_ctl0"+str(row)+"_imb_delete").click()
		wait.until(EC.alert_is_present())
		self.browser.switch_to.alert.accept()
		self.browser.switch_to.window(self.browser.window_handles[0])
		wait.until(lambda driver: len(self.browser.find_elements_by_css_selector("table#ctl00_ContentPlaceHolder1_MissingGridView .gridBody")) == rows-1)

	def doneKittingIncomplete(self, stm, pn):
		self.locateKit(stm, pn)
		wait = WebDriverWait(self.browser, 10)
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_btn_doneKitting")))
		wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
		wait.until(lambda driver: self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneKitting").is_enabled())
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneKitting").click()
		wait.until(lambda driver: self.browser.find_elements_by_id("ctl00_ContentPlaceHolder1_pnl_doneKitting_finishImport") or self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_incomplete"))
		if self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_pnl_doneKitting_finishImport").is_displayed():
			wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_btn_stillImporting")))
			self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_stillImporting").click()
		else:
			wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_btn_incomplete")))
			self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_incomplete").click()
			wait.until(EC.invisibility_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_pnl_doneKitting")))
			wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
			wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_btn_locateKit")))

	def receiveExtra(self, new_pn, kit_parent, qty, uom, is_kit, description):
		self.browser.get(self.CONST_HOST+"UApplication3/wh/lotrec/lotrecnewdetail.aspx?kit_parent="+str(kit_parent)+"&new_pn="+new_pn)
		wait = WebDriverWait(self.browser, 10)
		wait.until(EC.presence_of_element_located((By.ID, "txtLoc")))
		self.browser.find_element_by_id("txtLoc").send_keys("1")
		self.browser.find_element_by_id("txtConfirmPN").send_keys(str(new_pn))
		self.browser.find_element_by_id("txtBoxNo").send_keys("1")
		self.browser.find_element_by_id("txtQty").send_keys(str(qty))
		self.browser.find_element_by_xpath("//select[@name='ddlCond']/option[text()='NS']").click()
		if is_kit == "1":
			self.browser.find_element_by_id("chkIsKit").click()
		wait.until(lambda driver: self.browser.find_element_by_xpath("//input[@name='txtTaggedBy' and @disabled]"))
		self.browser.find_element_by_name("lblDesc").send_keys(str(description))
		self.browser.find_element_by_name("txtRemarks").send_keys("1")
		Select(self.browser.find_element_by_css_selector("select#ddlUOM")).select_by_value(str(uom))
		handles_before = self.browser.window_handles
		self.browser.find_element_by_id("btnSubmit").click()
		wait.until(lambda driver: len(handles_before) != len(driver.window_handles))
		self.browser.switch_to.window(self.browser.window_handles[1])
		self.browser.close()
		self.browser.switch_to.window(self.browser.window_handles[0])