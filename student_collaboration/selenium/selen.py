import os
import traceback
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import re

BASE_URL = "http://127.0.0.1:8000/"

ADMIN_PSEUDO = "root"
ADMIN_PASSWORD = "root"

TEACHER_PSEUDO = "TestTeacher"
TEACHER_PASSWORD = "test"
CLASS_NAME = "testClass"
STUDENTS = (
	("fnselen11", "lnselen11"),
	("fnselen22", "lnselen22")
)

STUDENTS_SKILLS = (
	{"mastered":("P3D-U3-T2", "P3D-U3-C2"), "unmastered":("P3D-U3-A2",)},   # Careful to master skill that other don't
	{"unmastered": ("P3D-U3-T2", "P3D-U3-C2"), "mastered": ("P3D-U3-A2",)}
)

STUDENT_ID = (
	1146,
	1147
)

STUDENTS_PASSWORD = "test"

STUDENTS_COLLABORATIVE_TOOLS_PARAMS = (
	(1180, 6),
	(1180, 7)
)


class Selenium:
	TIMEOUT_BUTTON_WAIT = 15
	def __init__(self):
		self.__initDriver()
		self.__hideDjangoDebug()

	def __initDriver(self):
		""" See readme file for more explication if trouble to install """
		if os.name == "nt":  # if it is a windows platform
			self.driver = webdriver.Chrome(r"chromedriver.exe")
		else:
			self.driver = webdriver.Chrome()
		self.driver.wait = WebDriverWait(self.driver, 1)

	def __hideDjangoDebug(self):
		""" Django DEbug Tab sometime overlap buttons that selenium try to click, so we hide it"""
		self.driver.get(BASE_URL)
		hideButton = self.__waitElementById("djHideToolBarButton")
		hideButton.click()


	def testAll(self):
		""" All tests """
		#self.testAdmin(ADMIN_PSEUDO, ADMIN_PASSWORD)

		self.testTeacherClassCreation(TEACHER_PSEUDO, TEACHER_PASSWORD, CLASS_NAME, STUDENTS, STUDENTS_SKILLS)

		studentsPseudo = self.testRegisterStudents()

		#studentsPseudo = ["fnselen11.lnselen116", "fnselen22.lnselen226"] # TODO : delete
		self.testCollaborativeTool(studentsPseudo, STUDENTS_COLLABORATIVE_TOOLS_PARAMS)



		#self.fakeTest()

	def testAdmin(self, admin_pseudo, admin_password):
		self.__testFunction(self.logInAdmin, admin_pseudo, admin_password)
		self.__testFunction(self.logOutAdmin)

	def testTeacherClassCreation(self, teacher_pseudo, teacher_password, class_name, students, students_skills):
		self.__testFunction(self.logInTeacher, teacher_pseudo, teacher_password)
		self.__testFunction(self.addClass, class_name)
		self.__testFunction(self.addStudents, students)
		self.__testFunction(self.setSkillsToStudent, students_skills)

	def testRegisterStudents(self):
		studentCodes = self.__testFunction(self.getStudentsCode)
		self.logOutUser()
		for studentUserName, studentCode in studentCodes.iteritems():
			self.__testFunction(self.logInStudent, studentUserName, STUDENTS_PASSWORD, studentCode)
			self.logOutUser()
		return studentCodes.keys()

	def testCollaborativeTool(self, studentsPseudo, students_collaborative_tools_params):
		# With the first user we create a help request
		curIndex = 0 # First student index
		self.__testFunction(self.logInStudent, studentsPseudo[curIndex], STUDENTS_PASSWORD)
		studentParams = students_collaborative_tools_params[curIndex]
		self.__testFunction(self.activateCollaborativeTool, studentParams[0], studentParams[1])
		# The first to connect ask for help
		askRequestText = self.__testFunction(self.askHelp)
		#print 'ask'+askRequestText
		self.logOutUser()

		# With the second one we check that the help request exists
		curIndex = 1 # We move to the second student
		self.__testFunction(self.logInStudent, studentsPseudo[curIndex], STUDENTS_PASSWORD)
		studentParams = students_collaborative_tools_params[curIndex]
		self.__testFunction(self.activateCollaborativeTool, studentParams[0], studentParams[1])
		self.__testFunction(self.acceptHelpRequest)
		self.logOutUser()

		# TODO : creer la discussion etc etc.

	def __testFunction(self, fun, *args):
		""" Test a given function on the given arguements"""
		functionName = fun.im_func.__name__
		print("Testing "+functionName+" with "+str(args)+" : ")
		try:
			ret = fun(*args)
			print("\tOK")
			return ret
		except TimeoutException as e:
			traceback.print_exc(e)
			print("\tERROR (Timeout) : "+ str(e.args) +" One of the demanded ressource took to much time to be found. It's likely that it didn't existed or the page wasn't loaded/redirected as expected")
		except WebDriverException as e:
			traceback.print_exc(e)
			print("\tError (WebDriver) : ") + str(e.args) + " The content have not beel loaded yet (need to call wait method)"
		except Exception as e:
			traceback.print_exc(e)
			print "\tERROR: " + str(e.args)
		except BaseException as e:
			traceback.print_exc(e)
			print "\tERROR: " + str(e.args)



	def __waitElementByName(self, name):
		return self.driver.wait.until(EC.presence_of_element_located((By.NAME, name)))

	def __waitElementByXPath(self, xPath):
		return self.driver.wait.until(EC.presence_of_element_located((By.XPATH, xPath)))

	def __waitElementByClassName(self, className):
		return self.driver.wait.until(EC.presence_of_element_located((By.CLASS_NAME, className)))

	def __waitElementByCSSSlector(self, css):
		return self.driver.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))

	def __waitElementById(self, id):
		return self.driver.wait.until(EC.presence_of_element_located((By.ID, id)))

	def __fillBoxSubmit(self, name, text):
		box = self.__fillBox(name, text)
		box.submit()

	def __fillBox(self, name, text):
		box = self.__waitElementByName(name)
		box.send_keys(text)
		return box

	def __countRawsInTable(self, xPathTable):
		return len(self.driver.find_elements_by_xpath(xPathTable+"/tbody/tr"))

	def __clickButtonByXPath(self, xPath):
		button = WebDriverWait(self.driver, self.TIMEOUT_BUTTON_WAIT).until(EC.element_to_be_clickable((By.XPATH, xPath)))
		# Do not try to create a parameter for this, it make crashs
		action = ActionChains(self.driver)
		action.click(button).perform()

	def __testURL(self, lastURL, *exceptionArgs):
		""" Test si l'url match l'URL courante """
		if not re.compile(BASE_URL + lastURL).match(self.driver.current_url):
			raise BaseException(*exceptionArgs)

	## Tests Methods ##

	def logInAdmin(self, adminPseudo, adminPassword):
		""" We consider that the given credentials already exists"""
		self.driver.get(BASE_URL+'admin/login/?next=/admin/')

		userNameBox = self.__waitElementByName("username")
		userNameBox.send_keys(adminPseudo)

		self.__fillBoxSubmit("password", adminPassword)

		self.__testURL("admin/", r"Admin page wasn't loaded", r"Are you sure that the superuser username and password given are corrects?")

	def logOutAdmin(self):
		self.driver.get(BASE_URL+'admin/logout')
		# If we were not connected we will be redirected, so it's not always true
		self.__testURL("admin/logout/", r"Can't logout admin session", r"Are you sure that you were logged in as a super user?")

	def logInTeacher(self, teacherPseudo, teacherPassword):
		""" We consider that the teacher already exists """
		self.__logInFirstStep(teacherPseudo)
		self.__testURL("accounts/passwordlogin/", r"The username passwords didn't show up",
		               r"Are you sure that this username aws created ?")
		# As a teacher the tag is "password" "code" for students
		self.__fillBoxSubmit("password", teacherPassword)
		self.__testURL("professor/dashboard/", r"Teacher have not be logged in sucessfully", "Are you sure that this teacher existed ?")


	def logOutUser(self):
		""" LogOut for both user and teacher"""
		self.driver.get(BASE_URL+'accounts/logout')
		# Nothing to check as it redirect us to homepage wherever we were previously connected or not

	def addClass(self, className):
		""" We consider that a teacher is currently logged in """
		self.driver.get(BASE_URL+'professor/lesson/add/')
		self.__fillBox("name", className)

		radioButton = self.__waitElementByName("stage")
		# Add a 6th year "enseignement professionnel (3e degre)"
		self.driver.execute_script(
			"document.evaluate(\"/html/body/div[2]/div[2]/div/div[2]/form/div[2]/div[2]/div[2]/ul[5]/li/div/label\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()")
		radioButton.submit()
		# Logically it contains with a regex but we skip this part
		self.__testURL("professor/lesson/[0-9]*/student/add/", "The add student page wasn't loaded sucessfully after adding the class")

	def addStudents(self, studentList):
		""" We consider that we are in the add student class page """

		# Watch out that on this page there is only 2 student that could be added
		# We can add extra student by clicking the +1 button, so we fake it
		for i in range(0, len(studentList)-2):
			xPathToAddOneStudent = '/html/body/div[2]/div[2]/div[6]/form/ul/li['+str(3+i)+']/button[1]'
			self.__clickButtonByXPath(xPathToAddOneStudent)

		# Fill the student form
		for i in range(len(studentList)):
			self.__fillBox("first_name_" + str(i), studentList[i][0])
			self.__fillBox("last_name_" + str(i), studentList[i][1])

		xPathSubmit = "/html/body/div[2]/div[2]/div[6]/form/div/button"
		self.__waitElementByXPath(xPathSubmit).submit()

		self.__testURL("professor/lesson/[0-9]*/", "You have not been redirected to the class dashboard")

	def setSkillsToStudent(self, studentSkillsList):
		""" We consider that we are on lesson dashboard """
		#self.driver.get("http://127.0.0.1:8000/professor/lesson/4") # TODO : to delete
		initUrl = self.driver.current_url
		# if we get the id of the first created student then it's easy to find the other one (just +1)
		xPathFirstTableEntry = '//*[@id="students"]/div[4]/div/table/tbody/tr[1]/td[1]/a'
		entry = self.__waitElementByXPath(xPathFirstTableEntry)#self.driver.find_element_by_xpath(xPathFirstTableEntry)
		href = entry.get_attribute("href")
		# get the id : 'http://127.0.0.1:8000/professor/lesson/1/student/1134/' -> 1134
		firstStudentIdStr = href[href[0:-2].rfind("/")+1:-1]
		firstStudentId = int(firstStudentIdStr)

		studentNumber = len(studentSkillsList)
		for i in range(studentNumber):
			studentId = firstStudentId+i
			urlToStudent = initUrl+"student/"+str(studentId)+"/"
			skillTab = "#heatmap"
			# We load the page where all its skills are
			self.driver.get(urlToStudent+skillTab)
			studentSkillsDict = studentSkillsList[i]
			for masteredStr, skillList in studentSkillsDict.iteritems():
				for skillStr in skillList:
					# We first make the popup appear

					# Be careful here to have an exact match, because after a skill is mastered it had invisible things with the name as well
					xPath = '//*[text()="{0}"]/..'.format(skillStr)
					# It won't appear if it is not in the scrolling view, so we center the button before clicking it
					button = self.__waitElementByXPath(xPath)
					centerY = button.location['y'] - self.driver.get_window_size()['height']//2
					self.driver.execute_script("window.scrollTo(0, " + str(centerY) + ");")

					self.__clickButtonByXPath(xPath)
#                   self.__clickButtonByXPath('//*[contains(text(), "{0}")]/..'.format(skillStr)) # DO NOT CALL, I don't know why but the function does not work there

					# As it appears we set the skill
					# The order is the one the buttons are displayed on the popup
					SKILL_MASTERED = 1
					SKILL_UNMASTERED = 2
					SKILL_UNKNOWN = 3
					if (masteredStr == "mastered"):
						skillIdx = SKILL_MASTERED
					else:
						skillIdx = SKILL_UNMASTERED
					test = self.__waitElementByClassName('popover-content')
					# Acess the correct button
					child = test.find_element_by_xpath("//div[2]/center/form[" + str(skillIdx) + "]")
					child.submit()

	def getStudentsCode(self):
		""" We consider that we are on a lesson page """
		self.driver.get("http://127.0.0.1:8000/professor/lesson/7/")# TODO : remove
		strDashbord = "professor/lesson/"
		url = self.driver.current_url
		professorDashbordURL = url[:url.find("/", url.find(strDashbord)+len(strDashbord))+1]
		codePage = professorDashbordURL+"students_password_page/"
		self.driver.get(codePage)
		table = self.driver.find_elements_by_xpath("/html/body/table")
		studentList = table[0].text.split()
		studentDict = {}
		for i in range(len(studentList) // 8):
			studentDict[studentList[4 + i * 8].decode()] = studentList[7 + i * 8].decode()
		return studentDict

	def __logInFirstStep(self, userName):
		self.driver.get(BASE_URL + "accounts/usernamelogin")
		self.__testURL("accounts/usernamelogin", r"You can't access the log in page", r"Are you sure that no user is already logged in ?")
		# First enter the log in
		self.__fillBoxSubmit("username", userName)


	def logInStudent(self, studentUserName, studentPassword, studentCode=None):
		"""
		Log in an existing student.
		We consider that no user is logged in already

		:param studentUserName: The student username
		:type studentUserName: str
		:param studentPassword: The stundent password, if he register for the first time, it will aso be the new password
		:type studentPassword: str
		:param studentCode: The student register code that the teacher know. It's mandatory if it is its  first registration
		:type studentCode: str
		"""
		self.__logInFirstStep(studentUserName)
		# If if is the code login page
		urlEnd = "/codelogin/"
		if self.driver.current_url.endswith(urlEnd):
			# Add to password entries
			self.__fillBoxSubmit("code", studentCode)
			self.__testURL("accounts/createpassword/", r"The student could not register his password", r"Was the student code correct correct ?")

			# New page asking password
			self.__fillBox("password", studentPassword)
			self.__fillBoxSubmit("confirmed_password", studentPassword)
		else: # Here the classic login page
			self.__fillBoxSubmit("password", studentPassword)
		self.__testURL("student/dashboard/", r"The student could not logged in to his dashboard", r"Was the password correct ?")


	def activateCollaborativeTool(self, postalCode, distance):
		""" We assume that a student user is currently logged in """
		self.driver.get(BASE_URL+"student_collaboration/settings/")
		self.__testURL("student_collaboration/settings/", r"The collaborative tool can't be accessed", r"Are you sure that a user is logged in already and that it is a student ?")

		# Enable the collaborative tool it is not already
		collaborativeCheckBox = self.__waitElementById("collaborative_tool_check")
		isAlreadyActivate = collaborativeCheckBox.is_selected()

		if not isAlreadyActivate:
			toggle = self.__waitElementByClassName("switch")
			toggle.click()
		else:
			print "\tWarning : The collaborative tool was already activated. It's content have still been refreshed"
		postalCodeBox = self.__waitElementByName("postal_code")
		postalCodeBox.send_keys(postalCode)

		distanceBox = self.__waitElementByName("distance")
		distanceBox.clear()
		distanceBox.send_keys(distance)

		distanceBox.submit()

	def askHelp(self):
		""" Will automatically ask help for his first unmastered skill.
		 We consider that the a student is logged in & have activated its collaborative tool & have at least one un mastered skill """
		self.driver.get(BASE_URL+"student_collaboration/request_help/")
		self.__testURL("student_collaboration/request_help/", r"The collaborative tool asking help page wasn't loaded properly", r"Are you sure that a student is logged in and already activate its contributive tool ?")

		# Make the dropdown appear
		dropdown = self.__waitElementByCSSSlector(".multiselect.dropdown-toggle.btn.btn-default")
		dropdown.click()
		# Check the checkbox of the first unmastered skill (to hard to find the corresponding skill)
		xPathFirstCheck = "/html/body/div[2]/div[3]/div/form/div/div/span/div/ul/li[1]/a/label/input"
		firstUnmasteredSkill = self.__waitElementByXPath(xPathFirstCheck)
		skillText = self.__waitElementByXPath("/html/body/div[2]/div[3]/div/form/div/div/span/div/ul/li[1]/a/label").text
		firstUnmasteredSkill.click()
		firstUnmasteredSkill.submit()
#		self.__waitElementById("send_help_request").click()
		# After submission we are redircted to the history tab
		try:
			self.__testURL("student_collaboration/help_request_history/", r"The help request history page was not shawn")
		except BaseException as e:
			print '\tWarning : The redirection to history failed, perhaps this help request already exists?'
		return skillText

	def acceptHelpRequest(self):
		""" Will automatically accept help requests
		We consider that the a student is logged in & have activated its collaborative tool & their is at least one, the first one will be accepted"""
		self.driver.get(BASE_URL+"student_collaboration/provide_help/")
		self.__testURL("student_collaboration/provide_help/", r"The collaborative tool asking help page wasn't loaded properly", r"Are you sure that a student is logged in and already activate its contributive tool ?")
		# Find the length of the table
		xPathTable = "//table[@id='provide-help']"
		sizeBeforeAcceptation = self.__countRawsInTable(xPathTable)


		# Find the accept button
		xPathTableText = '//*[@id="provide-help"]/tbody[2]/tr/td[2]/li'
		skillText = self.__waitElementByXPath(xPathTableText).text
		xPathFirstButton = '//*[@id="provide-help"]/tbody[2]/tr[1]/td[4]/button'
		# WARNING : it layout have not changed, the Accept button will probably be overlapped by the django debug tab
		# That's why we hide it on the object constructor
		self.__clickButtonByXPath(xPathFirstButton)

		if self.__countRawsInTable(xPathTable) != sizeBeforeAcceptation-1:
			raise BaseException(r"Table sized didn't decrement after request approval")
		return skillText


	def fakeTest(self):
		""" ca c'est juste pour faire des petit test vite fait """
		url = "http://127.0.0.1:8000/professor/lesson/4/student/1140/#heatmap"
		self.driver.get(url)


if __name__ == '__main__':
	selenium = Selenium()
	selenium.testAll()