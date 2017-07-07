class BitExtension:

	def revisionNameToLong(self, name):
		if name is None: return 0
		if name == "All" or name == "ALL": return -1
		if len(name) > 3:
			return 0
		index = 0
		while len(name) > 1:
			if name[0] != 'A':
				return 0
			name = name[1:]
			index += 26
		index += ord(name[0]) - ord('A')
		return self.toSignedLong(1 << (63-index))

	def longToBinaryString(self, long):
		return "{0:b}".format(long)

	def longToRevisionNameList(self, long):
		array = []
		bString = self.longToBinaryString(long)
		for i, char in bString:
			if char == '1':
				array.append(self.revisionIndexToRevisionName(i))
		return array

	def revisionIndexToRevisionName(self, index):
		if index >= 0 and index < 64:
			c = 'A'
			result = ""
			while index > 25:
				index -= 26
				result += "A"
			c = str(unichr(ord('A') + index))
			result += c
			return result
		else:
			return "N/A"

	def longToRevisionName(self, long):
		array = self.longToRevisionNameList(long)
		if len(array) > 0:
			return array[0]
		else:
			return "N/A"

	def toSignedLong(self, n):
		mask = (2 ** 63)-1
		if n & (1 << (64 - 1)): 
			return n | ~mask
		else:
			return n & mask

# if __name__ == "__main__":
# 	be = BitExtension()
# 	print(be.revisionNameToLong("A"))
# 	print(be.revisionNameToLong("B"))
# 	print(be.revisionNameToLong("C"))
# 	print(be.revisionNameToLong("D"))