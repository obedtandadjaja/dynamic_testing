import pyodbc
import random, string, time, os, sys

CONST_HOST = "http://localhost:58363/"
CONST_GET_IDENTITY = "SELECT @@IDENTITY"

class TestHelper:

	def __init__(self):
		self.db = None
		self.oracle = None
		self.stm_auto_key = 1

	@property
	def db(self):
		return self.db
	@property
	def oracle(self):
		return self.oracle
	@property
	def stm_auto_key(self):
		return self.stm_auto_key
	def db(self, value):
		self.db = value
	def oracle(self, value):
		self.oracle = value
	def stm_auto_key(self, value):
		self.stm_auto_key = value

	def wh_lots_receipt_insert(self, consig, po, pn, description, cond, receipt_qty, receipt_uom, loc, receipt_date, last_update_date, insp_by, app_code, remarks, box, is_kit, stm_auto_key):
		return (
			"Insert Into wh_lots_receipt (consig,po,pn,description,cond," +
			"receipt_qty,receipt_uom,loc,receipt_date,last_update_date,insp_by,app_code,remarks,box,is_kit,stm_auto_key)" +
			"Values(" +
			','.join([self.quote(consig), str(po), self.quote(pn), self.quote(description), self.quote(cond), str(receipt_qty), self.quote(receipt_uom), str(loc), self.quote(receipt_date), self.quote(last_update_date), self.quote(insp_by), self.quote(app_code), self.quote(remarks), str(box), str(is_kit), str(stm_auto_key)]) +
			");"
		)

	def kit_piece_part_list_insert(self, pn, master_pn, parent_pn, revision, subkit_revision, qty, uom, is_kit, description):
		master_pn = self.quote(str(master_pn)) if len(master_pn) > 0 else "NULL"
		parent_pn = self.quote(str(parent_pn)) if len(parent_pn) > 0 else "NULL"
		description = self.quote(str(description)) if len(description) > 0 else "NULL"
		return (
			"Insert into kit_piece_part_list (pn, master_pn, parent_pn, revision, subkit_revision, qty, uom, is_kit, description)" +
			"values(" +
			','.join([self.quote(pn), master_pn, parent_pn, str(revision), str(subkit_revision), str(qty), self.quote(str(uom)), str(is_kit), description]) +
			");"
		)

	def kit_piece_part_list_delete(self, pn):
		pn = self.quote(str(pn))
		return (
			"Delete from kit_piece_part_list where (pn = "+pn+" and master_pn is null and parent_pn is null) or (master_pn = "+pn+" and parent_pn = "+pn+");"
		)

	def kit_master_lookup_insert(self, subkit_pn, master_pn, subkit_revision, master_revision):
		subkit_pn = self.quote(str(subkit_pn))
		master_pn = self.quote(str(master_pn))
		return (
			"Insert into kit_master_lookup (subkit_pn, master_pn, subkit_revision, master_revision)" +
			"values(" +
			','.join([subkit_pn, master_pn, str(subkit_revision), str(master_revision)]) +
			");"
		)

	def generateRandomAlphanumeric(self, n):
		return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n))

	def generateRandomNumber(self, digits):
		return random.randint(10**(digits-1), 10**digits-1)

	def quote(self, string):
		return "'" + string + "'"
			
	def today(self):
		return time.strftime("%m/%d/%Y")

	def dbEstablishConnection(self):
		conn_str = (
		    r'Driver={SQL Server};'
		    r'Server=UASQLDEV;'
		    r'Database=unical;'
		    r'Trusted_Connection=yes;'
		 )
		self.db = pyodbc.connect(conn_str)

	def dbCloseConnection(self):
		self.db.close()

	def dbGetCursor(self):
		try:
			cursor = self.db.cursor()
			return cursor
		except Exception as e:
			if e.__class__ == pyodbc.ProgrammingError:
				self.db == self.dbEstablishConnection()
				cursor = self.db.cursor()
				return cursor

	def dbTestConnection(self):
		cursor = self.dbGetCursor()
		cursor.execute("SELECT 1")
		rows = cursor.fetchall()
		print("*** Successful connection ***" if len(rows) > 0 else "*** Unsuccessful connection ***")
		cursor.close()
		return len(rows) > 0

	def prepareTest(self):
		try:
			cursor = self.dbGetCursor()
			cursor.execute("DELETE FROM kit_list_missing")
			cursor.execute("DELETE FROM wh_lots_receipt where insp_by = 'otandadjaja'")
			cursor.execute("DELETE FROM kit_piece_part_list")
			cursor.execute("DELETE FROM kit_master_lookup")
			cursor.commit()
			cursor.close()
			print("---- database cleared ----\n")
		except Exception as e:
			print(e)
			print("---- Error! Failed to clear database ----\n")

	def insertMaster(self, pn, qty, uom, is_kit, description):
		insert_master = self.wh_lots_receipt_insert(
			"GEC-TDA141", 
			self.generateRandomNumber(5), 
			pn, 
			description, 
			"NS", 
			qty, 
			uom, 
			self.generateRandomNumber(2), 
			self.today(), 
			self.today(), 
			"otandadjaja", 
			"F", 
			"this is an auto-generated test", 
			self.generateRandomNumber(1), 
			is_kit,
			self.stm_auto_key
		)
		self.stm_auto_key += 1
		print(insert_master)
		cursor = self.dbGetCursor()
		cursor.execute(insert_master)
		cursor.commit()
		cursor.close()

	def getLatestSTM(self):
		cursor = self.dbGetCursor()
		cursor.execute("select top(1) stm_auto_key from unical.dbo.wh_lots_receipt where insp_by='otandadjaja' order by lots_receipt_id desc")
		row = cursor.fetchone()
		return row.stm_auto_key

	def getMissingLatestSTM(self):
		cursor = self.dbGetCursor()
		cursor.execute("select top(1) stm_auto_key from unical.dbo.kit_list_missing order by klm_auto_key desc")
		row = cursor.fetchone()
		return row.stm_auto_key

	def insertKitList(self, pn, master_pn, parent_pn, revision, subkit_revision, qty, uom, is_kit, description):
		insert_kit_list = self.kit_piece_part_list_insert(pn, master_pn, parent_pn, revision, subkit_revision, qty, uom, is_kit, description)
		print(insert_kit_list)
		cursor = self.dbGetCursor()
		cursor.execute(insert_kit_list)
		cursor.commit()
		cursor.close()

	def getKitList(self):
		cursor = self.dbGetCursor()
		cursor.execute("select * from unical.dbo.kit_piece_part_list")
		rows = cursor.fetchall()
		return rows

	def checkKitListExists(self, pn, master_pn, parent_pn, revision, subkit_revision, qty, uom, is_kit, description):
		cursor = self.dbGetCursor()
		master_pn = "="+self.quote(str(master_pn)) if len(str(master_pn)) > 0 else " is NULL"
		parent_pn = "="+self.quote(str(parent_pn)) if len(str(parent_pn)) > 0 else " is NULL"
		description = "="+self.quote(str(description)) if len(str(description)) > 0 else " is NULL"
		query = "select * from unical.dbo.kit_piece_part_list where pn='"+pn+"' and parent_pn"+parent_pn+" and master_pn"+master_pn+" and revision=cast("+revision+" as bigint) and subkit_revision=cast("+subkit_revision+" as bigint) and qty="+qty+" and uom="+self.quote(uom)+" and is_kit="+is_kit+" and description"+description+";"
		print(query)
		cursor.execute(query)
		rows = cursor.fetchall()
		return len(rows) > 0

	def insertKitLookup(self, subkit_pn, master_pn, subkit_revision, master_revision):
		insert_kit_lookup = self.kit_master_lookup_insert(subkit_pn, master_pn, subkit_revision, master_revision)
		print(insert_kit_lookup)
		cursor = self.dbGetCursor()
		cursor.execute(insert_kit_lookup)
		cursor.commit()
		cursor.close()

	def getMasterLookup(self):
		cursor = self.dbGetCursor()
		cursor.execute("select * from kit_master_lookup")
		rows = cursor.fetchall()
		return rows

	def checkMasterLookupExists(self, subkit_pn, master_pn, subkit_revision, master_revision):
		cursor = self.dbGetCursor()
		subkit_pn = str(subkit_pn)
		master_pn = str(master_pn)
		query = "select * from unical.dbo.kit_master_lookup where subkit_pn='"+subkit_pn+"' and master_pn='"+master_pn+"' and subkit_revision=cast("+subkit_revision+" as bigint) and master_revision=cast("+master_revision+" as bigint)"
		print(query)
		cursor.execute(query)
		rows = cursor.fetchall()
		return len(rows) > 0

	def deleteKitList(self, pn):
		delete_kit_list = self.kit_piece_part_list_delete(pn)
		print(delete_kit_list)
		cursor = self.dbGetCursor()
		cursor.execute(delete_kit_list)
		cursor.commit()
		cursor.close()

	def executeSelect(self, cmd):
		cursor = self.dbGetCursor()
		cursor.execute(cmd)
		rows = cursor.fetchall()
		cursor.close()
		return rows

	def getReceipt(self):
		cursor = self.dbGetCursor()
		cursor.execute("select pn, kit_revision, kit_status, is_kit from wh_lots_receipt where insp_by='otandadjaja'")
		rows = cursor.fetchall()
		return rows

	def getKitListMissing(self):
		cursor = self.dbGetCursor()
		cursor.execute("select * from kit_list_missing")
		rows = cursor.fetchall()
		return rows