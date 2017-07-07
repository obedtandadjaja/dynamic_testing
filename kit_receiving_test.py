from pprint import pprint
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
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.select import Select

# Kit Receiving
class KitReceivingTestCase(unittest.TestCase):
	filename = None
	CONST_HOST = None

	def setUp(self):
		self.browser = webdriver.Firefox()

	def getTestCase(self, file_path):
		with open(file_path) as data_file:
			data = json.load(data_file)
		return data

	def prepareTest(self, list, lookup, helper):
		helper.prepareTest()
		print("***SETTING UP EXISTING DATA IN KIT LIST***")
		for kitlist in list: 
			helper.insertKitList(kitlist["pn"], kitlist["master_pn"], kitlist["parent_pn"], kitlist["revision"], kitlist["subkit_revision"], kitlist["qty"], kitlist["uom"], kitlist["is_kit"], kitlist["description"])
		print("***DONE SETTING UP EXISTING DATA***")
		print("***SETTING UP EXISTING DATA IN KIT LIST***")
		for kitlookup in lookup:
			helper.insertKitLookup(kitlookup["subkit_pn"], kitlookup["master_pn"], kitlookup["subkit_revision"], kitlookup["master_revision"])
		print("***DONE SETTING UP EXISTING DATA***")

	def runTest(self):
		helper = TestHelper()
		helper.dbEstablishConnection()
		if helper.dbTestConnection() == False:
			return

		data = self.getTestCase("json_test_cases/"+self.filename)
		print("")
		print("=="*10)
		print("=*-"*5, data["_header"], "-*="*5)
		print("=="*10)
		print("")
		existing_list, existing_lookup, trees, matching_list, matching_lookup, matching_receipt = data["existing"]["list"], data["existing"]["lookup"], data["inserting"]["trees"], data["matching"]["list"], data["matching"]["lookup"], data["matching"]["receipt"]

		self.prepareTest(existing_list, existing_lookup, helper)

		if len(trees) > 0:
			for tree in trees:
				tree["stm_auto_key"] = helper.stm_auto_key
				helper.insertMaster(tree["pn"], tree["qty"], tree["uom"], tree["is_kit"], tree["description"])
				self.login()
				self.locateKit(tree["stm_auto_key"], tree["pn"])
				print("***START RECEIVING***")
				self.startReceiving(tree, helper)
				print("***END RECEIVING***")

		print("***BEGIN COMPARE MATCHING***")
		rows = helper.getKitList()
		self.assertEqual(len(rows), len(matching_list), msg="Number of rows in matching list does not match number of rows in kit_piece_part_list table")
		for kitlist in matching_list:
			self.assertTrue(helper.checkKitListExists(kitlist["pn"], kitlist["master_pn"], kitlist["parent_pn"], kitlist["revision"], kitlist["subkit_revision"], kitlist["qty"], kitlist["uom"], kitlist["is_kit"], kitlist["description"]), msg=kitlist["pn"]+" does not exist")
		rows = helper.getMasterLookup()
		self.assertEqual(len(rows), len(matching_lookup), msg="Number of rows in matching lookup does not match number of rows in kit_master_lookup table")
		for kitlookup in matching_lookup:
			self.assertTrue(helper.checkMasterLookupExists(kitlookup["subkit_pn"], kitlookup["master_pn"], kitlookup["subkit_revision"], kitlookup["master_revision"]))
		rows = helper.getReceipt()
		self.assertEqual(len(rows), len(matching_receipt), msg="Number of rows in matching receipt does not match number of rows in wh_lots_receipt")
		for row in rows:
			rowMatched = False
			index = 0
			for rec in matching_receipt:
				if row.pn == rec["pn"] and row.kit_revision == rec["kit_revision"] and row.kit_status == rec["kit_status"] and row.is_kit == (rec["is_kit"] == "1"):
					del matching_receipt[index]
					rowMatched = True
					break
				index += 1
			if not rowMatched:
				print(row.pn, row.kit_revision, row.kit_status, row.is_kit)
				pprint(matching_receipt)
			self.assertTrue(rowMatched, msg="matching_receipt: Row does not match")
		self.assertEqual(len(matching_receipt), 0, msg="matching_receipt: not all records matched the ones in wh_lots_receipt")
		print("***END COMPARE MATCHING***")

		helper.dbCloseConnection()

	def startReceiving(self, current, helper):
		for child in current["children"]:
			print(child["pn"], current["stm_auto_key"], child["qty"], child["uom"], child["is_kit"], child["description"])
			if child["is_missing"]:
				if current["is_missing"]:
					self.receiveMissing(child, current, bypass=True)
				else:
					self.receiveMissing(child, current)
				try:
					child["stm_auto_key"] = helper.getMissingLatestSTM()
				except Exception as e:
					child["stm_auto_key"] = helper.getMissingLatestSTM()
			else:
				self.receiveExtra(child["pn"], current["stm_auto_key"], child["qty"], child["uom"], child["is_kit"], child["description"])
				try:
					child["stm_auto_key"] = helper.getLatestSTM()
				except Exception as e:
					child["stm_auto_key"] = helper.getLatestSTM()
			self.startReceiving(child, helper)
		if current["is_kit"] == "1":
			self.doneKittingComplete(current["stm_auto_key"], current["pn"])

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

	def inputMissing(self, node, parent):
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

	def doneKittingIncomplete(self, stm, pn):
		self.locateKit(stm, pn)
		wait = WebDriverWait(self.browser, 10)
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_btn_doneKitting")))
		wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
		wait.until(lambda driver: self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneKitting").is_enabled())
		try:
			self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MissingGridView")
		except Exception:
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

	def doneKittingComplete(self, stm, pn):
		self.locateKit(stm, pn)
		wait = WebDriverWait(self.browser, 10)
		wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_btn_doneKitting")))
		wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
		wait.until(lambda driver: self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneKitting").is_enabled())
		self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneKitting").click()
		wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
		self.doneKittingCompleteStep1(wait)

	"""
	complete or doneimporting
	"""
	def doneKittingCompleteStep1(self, wait):
		# wait.until(lambda driver: self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneImporting") or self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_complete"))
		# try:
		# 	wait.until(lambda driver: self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneImporting").is_displayed() or self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_complete").is_displayed())
		# except Exception:
		# 	self.doneKittingCompleteStep1(wait)
		# 	return
		try:
			self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneImporting").click()
			wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
			try:
				self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MainGridView")
				self.doneKittingCompleteStep2(wait)
			except Exception as e:
				wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
				try:
					self.browser.find_elements_by_id("ctl00_ContentPlaceHolder1_btn_doneKitting_confirm")
					self.doneKittingCompleteStep2(wait)
				except Exception as e:
					return
		except Exception as e:
			try:
				self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_complete").click()
			except Exception:
				self.doneKittingCompleteStep1(wait)
				return
			wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
			self.doneKittingCompleteStep2(wait)

	"""
	confirm or alert click
	"""
	def doneKittingCompleteStep2(self, wait):
		# wait.until(lambda driver: self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneKitting_confirm") or EC.alert_is_present())
		# try:
		# 	wait.until(lambda driver: self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneKitting_confirm").is_displayed() or EC.alert_is_present())
		# except Exception:
		# 	self.doneKittingCompleteStep2(wait)
		# 	return
		try:
			self.browser.switch_to.alert.accept()
			self.browser.switch_to.window(self.browser.window_handles[0])
		except Exception as e:
			try:
				self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btn_doneKitting_confirm").click()
			except Exception:
				self.doneKittingCompleteStep2(wait)
				return
			wait.until(EC.invisibility_of_element_located((By.ID, "ct100_ContentPlaceHolder1_img_loading")))
			try:
				self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_MainGridView")
				WebDriverWait(self.browser, 10).until(EC.alert_is_present())
				self.browser.switch_to.alert.accept()
			except Exception as e:
				return

	def receive(self, pn, kit_parent, description, uom, is_kit):
		self.browser.get(self.CONST_HOST+"UApplication3/wh/lotrec/lotrecnewdetail.aspx?pn="+pn+"&kit_parent="+kit_parent+"&description="+description+"&uom"+uom+"&is_kit"+is_kit)
		wait = WebDriverWait(self.browser, 10)
		wait.until(lambda driver: self.browser.current_url != self.CONST_HOST+"UApplication3/wh/lotrec/lotrecnewdetail.aspx?kit_parent="+kit_parent+"&new_pn="+new_pn)

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

	"""
	Test for login
	"""
	def login(self):
		self.browser.get(self.CONST_HOST+"UApplication3/login.aspx")
		userName = self.browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserName")
		userName.clear()
		userName.send_keys("oTandadjaja")
		password = self.browser.find_element_by_name("ctl00$ContentPlaceHolder1$Password")
		password.clear()
		password.send_keys(PASSWORD)
		login = self.browser.find_element_by_name("ctl00$ContentPlaceHolder1$LoginImageButton")
		login.click()
		current_url = self.browser.current_url
		wait = WebDriverWait(self.browser, 10)
		wait.until(lambda driver: self.browser.current_url != self.CONST_HOST+"UApplication3/login.aspx")
		self.assertNotIn("User Login", self.browser.title)
		